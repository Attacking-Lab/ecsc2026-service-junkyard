package main

import (
	"bufio"
	"fmt"
	"maps"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"sync"
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

type Dictionary struct {
	words map[uint64]map[string]struct{}
}

func NewDictionary() *Dictionary {
	return &Dictionary{
		words: make(map[uint64]map[string]struct{}),
	}
}

var dictionaries = make(map[string]*Dictionary)
var dictionariesLock = sync.Mutex{}

func GetDictionary(language string) (*Dictionary, error) {
	dictionariesLock.Lock()
	defer dictionariesLock.Unlock()

	if dictionary, ok := dictionaries[language]; ok {
		return dictionary, nil
	}
	dictionary := NewDictionary()
	err := dictionary.LoadDictionary(language)
	if err != nil {
		return nil, err
	}
	dictionaries[language] = dictionary
	return dictionary, nil
}

func (dict *Dictionary) LoadDictionary(language string) error {
	filePath := filepath.Join(LangDir, language+".txt")

	file, err := os.Open(filePath)
	if err != nil {
		return err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if len(line) > 1 {
			dict.AddWord(line)
		}
	}

	if err = scanner.Err(); err != nil {
		return err
	}

	return nil
}

func (dict *Dictionary) AddWord(word string) {
	hashes := HashWordAll(word)
	for _, hash := range hashes {
		if hash > 0 {
			if innerMap, ok := dict.words[hash]; !ok {
				dict.words[hash] = make(map[string]struct{})
				dict.words[hash][word] = struct{}{}
			} else {
				innerMap[word] = struct{}{}
			}
		}
	}
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
	innerMap0 := dict.words[hashes[0]]
	if innerMap0 != nil {
		if _, ok := innerMap0[word]; ok {
			return true, nil
		}
		if len(innerMap0) > 0 && len(innerMap0) <= limit {
			return false, slices.Collect(maps.Keys(innerMap0))
		}
	}
	result := make([]string, 0)
	for _, hash := range hashes[1:] {
		innerMap := dict.words[hash]
		if innerMap != nil {
			if len(innerMap) > 0 && len(innerMap) <= limit-len(result) {
				result = append(result, slices.Collect(maps.Keys(innerMap))...)
			} else if len(innerMap) > 0 {
				return false, nil // too many suggestions
			}
		}
	}
	return false, result
}

func getDictionaryCharPoint(c rune) int32 {
	if c >= 32 && c <= 46 {
		return c - 32 + 1
	}
	if c >= 65 && c <= 90 {
		return c - 65 + 16
	}
	if c >= 97 && c <= 122 {
		return c - 97 + 16
	}
	if c >= 223 && c <= 255 {
		return c - 223 + 42
	}
	if c >= 1072 && c <= 1119 {
		return (c-1072)/2 + 75
	}
	if c >= 940 && c <= 993 {
		return (c-940)/4 + 99
	}
	if c >= 1376 && c <= 1416 {
		return (c-1376)/4 + 113
	}
	if c >= 0x100 && c <= 0x17f {
		return (c-0x100)/2 + 124
	}
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
