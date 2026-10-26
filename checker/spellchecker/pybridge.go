package main

// C interface for spellchecker.go, loaded from Python via ctypes (see __init__.py).
// Build: go build -buildmode=c-shared -o libspellchecker.so .

/*
#include <stdlib.h>
*/
import "C"

import (
	"errors"
	"strings"
	"unsafe"
)

// ctypes releases the GIL during calls. The loaded index is immutable, so spellchecks can run concurrently.

// LoadIndex maps the precomputed dictionary index (see index.go). Returns 0 on success, 1 on error.
// On error, *out receives the error message, it must be released with FreeString.
//
//export LoadIndex
func LoadIndex(path *C.char, out **C.char) C.int {
	if err := loadIndex(C.GoString(path)); err != nil {
		*out = C.CString(err.Error())
		return 1
	}
	*out = nil
	return 0
}

// SpellcheckC returns 0 on success, 1 on error. *out receives the result or the error message,
// it must be released with FreeString.
//
//export SpellcheckC
func SpellcheckC(text *C.char, language *C.char, confidence C.double, out **C.char) C.int {
	result, err := Spellcheck(C.GoString(text), C.GoString(language), float64(confidence))
	if err != nil {
		*out = C.CString(err.Error())
		return 1
	}
	*out = C.CString(result)
	return 0
}

// HasDictionaries checks that the loaded index contains all languages (newline-separated).
// Returns 0 on success, 1 on error (*out as in LoadIndex).
//
//export HasDictionaries
func HasDictionaries(languages *C.char, out **C.char) C.int {
	var errs []error
	for language := range strings.SplitSeq(C.GoString(languages), "\n") {
		_, err := GetDictionary(language)
		errs = append(errs, err)
	}
	if err := errors.Join(errs...); err != nil {
		*out = C.CString(err.Error())
		return 1
	}
	*out = nil
	return 0
}

//export FreeString
func FreeString(s *C.char) {
	C.free(unsafe.Pointer(s))
}
