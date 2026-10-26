import random
import time
from collections import defaultdict
from pathlib import Path

from flag_image_generator import rnd_flag
from text_utils import LANGUAGES, Language, get_language, spellcheck


def load_interesting_strings() -> list[str]:
    c = (Path(__file__).parent.parent / "res" / "interesting_strings.txt").read_text("utf-8")
    return [x.strip() for x in c.split("\n") if x.strip()]

INTERESTING_STRINGS: list[str] = load_interesting_strings()


def gen_interesting_string() -> str:
    return random.choice(INTERESTING_STRINGS)


def gen_text_with_flag(flag: str) -> tuple[Language, str]:
    language = random.choice(list(LANGUAGES.values()))
    sentences = [random.choice(language.sentences) for _ in range(random.randint(3, 20))]
    sentences += [random.choice(list(language.words)) for _ in range(random.randint(0, 3))]
    if flag:
        sentences.append(flag)
    random.shuffle(sentences)
    return language, "\n".join(sentences)


def gen_text_with_flag_checked(flag: str, required_in_spellchecker_result: bool = True, min_confidence: float = 0.0) -> tuple[Language, str]:
    """Ensure that the generated text detects as the intended language."""
    while True:
        language, text = gen_text_with_flag(flag)
        language2, confidence = get_language(text)
        if confidence <= min_confidence:
            print(f"Got confidence {confidence} instead of at least {min_confidence}, re-attempting...")
            continue
        if language != language2:
            print(f"Got {language2} instead of {language}, re-attempting...")
            continue
        spellcheck_result = spellcheck(text, language, 0.0)
        if flag and required_in_spellchecker_result and flag not in spellcheck_result:
            print("Too many errors in spellchecking, re-attempting...")
            continue
        return language, text


def check_text_generation_language_matches() -> None:
    print(f"===== check_text_generation_language_matches =====")
    count = 5000
    errors = 0
    sum_confidence: float = 0.0
    min_confidence: float = 100000
    t = time.monotonic()
    per_language: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for _ in range(count):
        language, text = gen_text_with_flag(rnd_flag())
        per_language[language.name][0] += 1
        language2, confidence = get_language(text)
        if language != language2:
            errors += 1
            per_language[language.name][1] += 1
            print(f"- expected {language.name} but was {language2.name}")
        else:
            sum_confidence += confidence
            min_confidence = min(min_confidence, confidence)
    t = time.monotonic() - t
    print(
        f"Errors: {errors} / {count} ({errors / count * 100:.3f}% error rate, {(count - errors) / count * 100:.3f}% success rate)")
    print(f"Average confidence: {sum_confidence / (count - errors) * 100:.3f}%")
    print(f"Min confidence: {min_confidence * 100:.3f}%")
    print(f"Generation + check time: {t / count * 1000.0:.2f}ms per entry")

    for language_name, (total, errors) in sorted(per_language.items()):
        print(f"- {errors / total * 100:6.3f}% error rate | {language_name} ({errors} / {total})")


def check_text_generation_outputs_flag() -> None:
    print(f"===== check_text_generation_outputs_flag =====")
    count = 5000
    errors = 0
    t = time.monotonic()
    for _ in range(count):
        flag = rnd_flag()
        language, text = gen_text_with_flag(flag)
        result = spellcheck(text, language, 0.0)
        if flag not in result:
            errors += 1
            if False:
                print("=" * 80 + " " + str(language))
                print(text)
                print("=" * 80)
                print(result)
                print("=" * 80 + "\n\n")
                # break

    t = time.monotonic() - t
    print(
        f"Errors: {errors} / {count} ({errors / count * 100:.3f}% error rate, {(count - errors) / count * 100:.3f}% success rate)")
    print(f"Generation + spellcheck time: {t / count * 1000.0:.2f}ms per entry")


if __name__ == "__main__":
    print(f"{len(LANGUAGES)} languages loaded...")
    check_text_generation_language_matches()
    check_text_generation_outputs_flag()
