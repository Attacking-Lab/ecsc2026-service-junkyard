package main

import (
	"fmt"
	"strings"
)

func Spellcheck(text string, language string, confidence float64) (string, error) {
	result := fmt.Sprintf("SpellChecker v0.9.1a\nLanguage is %s (confidence: %.1f)\n", language, confidence*100.0)

	dictionary, err := GetDictionary(language)
	if err != nil {
		return "", err
	}

	errors := 0
	for word := range strings.FieldsFuncSeq(text, func(r rune) bool { return strings.ContainsRune(" \n\t.,;:!?\"()%„“«»", r) }) {
		if len(word) > 1 {
			ok, suggestions := dictionary.CheckWord(word, 5)
			if !ok {
				errors++
				result += fmt.Sprintf("\nInvalid word: '%s'\n", word)
				if len(suggestions) > 0 {
					result += fmt.Sprintf("Did you mean one of: '%s'?\n", strings.Join(suggestions, "', '"))
				}
				if errors > 10 {
					result += "\nToo many errors, did not check further."
					break
				}
			}
		}
	}
	if errors == 0 {
		result += "\nText is correct."
	}

	return result, nil
}

func isNumeric(s string) bool {
	for _, c := range s {
		if c < '0' || c > '9' {
			return false
		}
	}
	return len(s) > 0
}

func (dict *Dictionary) CheckWord(word string, limit int) (bool, []string) {
	// pure numeric words should not be an error!
	if word == "" || isNumeric(word) {
		return true, nil
	}

	hashes := HashWordAll(word)
	if bucket0, ok := dict.bucket(hashes[0]); ok {
		if dict.bucketContains(bucket0, word) {
			return true, nil
		}
		if len(bucket0) <= limit {
			return false, dict.bucketWords(bucket0)
		}
	}
	result := make([]string, 0)
	for _, hash := range hashes[1:] {
		if b, ok := dict.bucket(hash); ok {
			if len(b) <= limit-len(result) {
				result = append(result, dict.bucketWords(b)...)
			} else {
				return false, nil // too many suggestions
			}
		}
	}
	return false, result
}

// getDictionaryCharPoint maps a character to a value < 256 for the dictionary hash.
// Same as getCharPoint in language-tool/source/stats.d (values < 124), plus the Latin Extended ranges.
// Keep in sync with get_dictionary_char_point in the checker.
func getDictionaryCharPoint(c rune) int32 {
	// 1-15
	if c >= 32 && c <= 46 {
		return c - 32 + 1
	}
	// 16-41
	if c >= 65 && c <= 90 {
		return c - 65 + 16
	}
	if c >= 97 && c <= 122 {
		return c - 97 + 16
	}
	// 42-74
	if c >= 223 && c <= 255 {
		return c - 223 + 42
	}
	// 75-98
	if c >= 1072 && c <= 1119 {
		return (c-1072)/2 + 75
	}
	// 99-112
	if c >= 940 && c <= 993 {
		return (c-940)/4 + 99
	}
	// 113-123
	if c >= 1376 && c <= 1416 {
		return (c-1376)/4 + 113
	}
	// 124-187: Latin Extended-A (lowercase letters are every other code point)
	if c >= 0x100 && c <= 0x17f {
		return (c-0x100)/2 + 124
	}
	// 188-239: Latin Extended-B
	if c >= 0x180 && c <= 0x24f {
		return (c-0x180)/4 + 188
	}
	return 0
}

func HashWordMain(word string) uint64 {
	word = strings.ToLower(word)
	hash := uint64(0)
	i := 0
	for _, c := range word {
		hash |= uint64(getDictionaryCharPoint(c)) << (i * 8)
		if i >= 6 {
			break
		}
		i += 1
	}
	return hash
}

func HashWordAll(word string) []uint64 {
	basehash := HashWordMain(word)

	hashes := make([]uint64, 1)
	hashes[0] = basehash

	// single wrong character
	for i := range 7 {
		h := basehash & ^(0xff << (i * 8))
		if h != basehash {
			hashes = append(hashes, h)
		}
	}

	// single missing/additional character
	for i := range 7 {
		p := (uint64(1) << (i * 8)) - 1 // 0, 0xff, 0xffff, ...
		h := (basehash >> 8 & ^p) | (basehash & p)
		if h != basehash {
			hashes = append(hashes, h)
		}
	}

	return hashes
}
