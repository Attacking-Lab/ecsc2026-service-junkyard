import os
import re
import sys
from pathlib import Path

LANGUAGES_DIR = Path(__file__).parent.parent / "res" / "languages"
LANGUAGES_ADDITIONAL_DIR = Path(__file__).parent.parent / "res" / "languages-additional"
LANGUAGE_NAMES = [f.stem for f in LANGUAGES_DIR.glob("*.txt")]

USE_GO_SPELLCHECKING = True


def sanitize_text(s: str) -> str:
    # replace some "special spaces" and unprintables that mess with Go vs. Python
    s = s.replace('\xad', '')  # soft hypen
    s = s.replace('\uf027', '')  # undefined
    s = s.replace('\uf02c', '')  # undefined
    s = s.replace('\u2006', ' ')
    s = s.replace('\u2008', ' ')
    s = s.replace('\u2009', ' ')
    s = s.replace('\u200a', ' ')
    s = s.replace('\u200b', ' ')
    s = s.replace('\u200c', ' ')
    s = s.replace('\u200d', ' ')
    s = s.replace('\u200e', ' ')
    s = s.replace('\u200f', ' ')
    s = s.replace('\u202c', ' ')
    s = s.replace('\u202d', ' ')
    s = s.replace('\u202f', ' ')
    s = s.replace('\u2060', ' ')
    s = s.replace('\u3000', ' ')
    s = s.replace('\ufeff', ' ')
    s = s.strip()
    return s


class Language:
    def __init__(self, name: str) -> None:
        self.name = name
        self._words: list[str] = []
        self._sentences: list[str] = []
        self._weights: list[int] = []
        self._dictionary: Dictionary | None = None

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Language) and self.name == other.name

    def __repr__(self) -> str:
        return f"Language({self.name})"

    def __str__(self) -> str:
        return f"Language {self.name}"

    def _load(self, f: Path, sanitize: bool = False) -> list[str]:
        content = f.read_text()
        if sanitize:
            content = sanitize_text(content)
        return [x.strip() for x in content.splitlines(keepends=False) if x]

    @property
    def words(self) -> list[str]:
        if not self._words:
            self._words = self._load(LANGUAGES_DIR / f"{self.name}.txt")
        return self._words

    @property
    def sentences(self) -> list[str]:
        if not self._sentences:
            self._sentences = self._load(LANGUAGES_ADDITIONAL_DIR / f"{self.name}-sentences.txt", sanitize=True)
        return self._sentences

    @property
    def weights(self) -> list[int]:
        if not self._weights:
            raw = (LANGUAGES_DIR / f"{self.name}.stat").read_bytes()
            self._weights = [int.from_bytes(raw[i:i + 4], byteorder="little") for i in range(0, len(raw), 4)]
            if len(self._weights) != CHAR_DIM_SIZE * CHAR_DIM_SIZE:
                raise ValueError(f"Invalid weights for {self.name}")
        return self._weights

    @property
    def dictionary(self) -> Dictionary:
        if self._dictionary is None:
            self._dictionary = Dictionary(self.words)
        return self._dictionary


LANGUAGES: dict[str, Language] = {name: Language(name) for name in LANGUAGE_NAMES}

CHAR_DIM_SIZE = 124


def get_char_point(c: str) -> int:
    """Convert a character to a point value (0-123)."""
    code = ord(c)
    # 1-15
    if 32 <= code <= 46:
        return code - 32 + 1
    # 16-41
    if 65 <= code <= 90:
        return code - 65 + 16
    if 97 <= code <= 122:
        return code - 97 + 16
    # 42-74
    if 223 <= code <= 255:
        return code - 223 + 42
    # 75-98
    if 1072 <= code <= 1119:
        return (code - 1072) // 2 + 75
    # 99-112
    if 940 <= code <= 993:
        return (code - 940) // 4 + 99
    # 113-123
    if 1376 <= code <= 1416:
        return (code - 1376) // 4 + 113
    # TODO keep in sync with D code!

    return 0


def count_digrams(text: str) -> list[int]:
    """Count character digrams (two-character sequences) in the text."""
    counts = [0] * (CHAR_DIM_SIZE * CHAR_DIM_SIZE)

    last_point = 0
    for c in text:
        point = get_char_point(c)
        if point != 0 and last_point != 0:
            counts[last_point * CHAR_DIM_SIZE + point] += 1
        last_point = point

    return counts


def distribution(data: list[int]) -> list[int]:
    """Normalize the distribution to fit within int32 range."""
    total = sum(data)
    if total > 0:
        factor = (2 ** 31 - 1) / total  # int.max in D is 2^31 - 1
        data = [round(item * factor) for item in data]
    return data


def similarity(dist1: list[int], dist2: list[int]) -> float:
    """Calculate similarity between two distributions."""
    result = 1.0
    for v1, v2 in zip(dist1, dist2):
        d = abs(v1 - v2)
        result *= 1 / (d / 100000000.0 + 1)

    return pow(result, 0.1)


def get_language(text: str) -> tuple[Language, float]:
    stat = distribution(count_digrams(text))
    similarities = {
        lang: similarity(stat, lang.weights)
        for lang in LANGUAGES.values()
    }
    return max(similarities.items(), key=lambda x: x[1])


class Dictionary:
    def __init__(self, wordlist: list[str]):
        # Most buckets contain a single word, which is stored as plain str instead of a set (saves most of the memory)
        self.words: dict[int, str | set[str]] = {}
        for word in wordlist:
            if len(word.encode("utf-8")) > 1:
                self.add_word(word)

    def add_word(self, word: str) -> None:
        hashes = hash_word_all(word)
        for hash_val in hashes:
            if hash_val > 0:
                bucket = self.words.get(hash_val)
                if bucket is None:
                    self.words[hash_val] = word
                elif isinstance(bucket, str):
                    if bucket != word:
                        self.words[hash_val] = {bucket, word}
                else:
                    bucket.add(word)

    def check_word(self, word: str, limit: int) -> tuple[bool, list[str]]:
        # pure numeric words should not be an error!
        if word == "" or (word.isnumeric() and word.isascii()):
            return True, []

        hashes = hash_word_all(word)
        bucket_0 = self.words.get(hashes[0])
        if bucket_0 is not None:
            if _bucket_contains(bucket_0, word):
                return True, []
            if _bucket_len(bucket_0) <= limit:
                return False, _bucket_words(bucket_0)

        result: list[str] = []
        for hash_val in hashes[1:]:
            bucket = self.words.get(hash_val)
            if bucket is not None:
                if _bucket_len(bucket) <= limit - len(result):
                    result.extend(_bucket_words(bucket))
                else:
                    return False, []  # too many suggestions

        return False, result


def _bucket_contains(bucket: str | set[str], word: str) -> bool:
    return bucket == word if isinstance(bucket, str) else word in bucket


def _bucket_len(bucket: str | set[str]) -> int:
    return 1 if isinstance(bucket, str) else len(bucket)


def _bucket_words(bucket: str | set[str]) -> list[str]:
    return [bucket] if isinstance(bucket, str) else list(bucket)


def get_dictionary_char_point(c: str) -> int:
    """Convert a character to a point value (0-239) for the dictionary hash: get_char_point plus Latin Extended.
    Keep in sync with getDictionaryCharPoint in the Go spellchecker."""
    code = ord(c)
    # 124-187: Latin Extended-A (lowercase letters are every other code point)
    if 0x100 <= code <= 0x17f:
        return (code - 0x100) // 2 + 124
    # 188-239: Latin Extended-B
    if 0x180 <= code <= 0x24f:
        return (code - 0x180) // 4 + 188
    return get_char_point(c)


def hash_word_main(word: str) -> int:
    word = word.lower()
    hash_val = 0
    for i, c in enumerate(word):
        hash_val |= get_dictionary_char_point(c) << (i * 8)
        if i >= 6:
            break
    return hash_val


def hash_word_all(word: str) -> list[int]:
    basehash = hash_word_main(word)

    hashes = [basehash]

    # single wrong character
    for i in range(7):
        h = basehash & ~(0xff << (i * 8))
        if h != basehash:
            hashes.append(h)

    # single missing/additional character
    for i in range(7):
        p = (1 << (i * 8)) - 1  # 0, 0xff, 0xffff, ...
        h = ((basehash >> 8) & ~p) | (basehash & p)
        if h != basehash:
            hashes.append(h)

    return hashes


def spellcheck(text: str, language: Language, confidence: float) -> str:
    if USE_GO_SPELLCHECKING:
        return spellcheck_go(text, language, confidence)

    result = f"SpellChecker v0.9.1a\nLanguage is {language.name} (confidence: {confidence * 100.0:.1f})\n"

    dictionary = language.dictionary

    errors = 0
    words = re.split(r'[ \n\t.,;:!?"()%„“«»]', text)
    for word in words:
        if len(word.encode("utf-8")) > 1:
            ok, suggestions = dictionary.check_word(word, 5)
            if not ok:
                errors += 1
                result += f"\nInvalid word: '{word}'\n"
                if len(suggestions) > 0:
                    result += "Did you mean one of: '" + "', '".join(suggestions) + "'?\n"
                if errors > 10:
                    result += "\nToo many errors, did not check further."
                    break

    if errors == 0:
        result += "\nText is correct."

    return result


def parse_spellchecker_output(output: str) -> list[str | set[str]]:
    result: list[str | set[str]] = []
    for line in output.splitlines():
        m = re.match(r"^Did you mean one of: '(.*)'\?$", line)
        if m:
            result.append(set(m.group(1).split("', '")))
        else:
            result.append(line)
    return result


def spellcheck_go(text: str, language: Language, confidence: float) -> str:
    from spellchecker import Spellcheck
    return Spellcheck(text, language.name, confidence)


def init() -> None:
    """Map the precomputed dictionary index and check that it contains all languages. Call after forking."""
    if not USE_GO_SPELLCHECKING:
        return
    from spellchecker import ensure_dictionaries_loaded
    ensure_dictionaries_loaded(list(LANGUAGES))
    print(f"[{os.getpid()}] Initialized spellchecker dictionaries", file=sys.stderr)
