package main

// Precomputed dictionary index: all dictionaries are hashed at build time (see main.go) into one immutable file,
// which is mmap'ed at runtime. Opening it takes less than a millisecond (instead of seconds of CPU and gigabytes of
// heap per process), and all processes share the same pages via the page cache.
//
// File layout (little endian, all sections 8-byte aligned):
//   header:  magic [8]byte, nLanguages uint64
//   table:   nLanguages * {name [16]byte (zero padded), offset uint64, size uint64}
//   section: one per language (see buildSection)

import (
	"bufio"
	"bytes"
	"cmp"
	"encoding/binary"
	"errors"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"unsafe"
)

var indexMagic = [8]byte{'S', 'P', 'E', 'L', 'L', 'I', 'D', 1}

const (
	indexHeaderSize   = 16
	indexEntrySize    = 32
	indexMaxNameLen   = 16
	sectionHeaderSize = 32
)

// Dictionary is a read-only view into a mapped index section. Words are grouped in buckets by hash
// (every word is in the buckets of all hashes from HashWordAll).
type Dictionary struct {
	keys     []uint64 // sorted unique hashes
	starts   []uint32 // bucket of keys[i]: refs[starts[i]:starts[i+1]]
	refs     []uint32 // word indices
	wordOffs []uint32 // word i: blob[wordOffs[i]:wordOffs[i+1]]
	blob     []byte
}

func (dict *Dictionary) bucket(hash uint64) ([]uint32, bool) {
	i, ok := slices.BinarySearch(dict.keys, hash)
	if !ok {
		return nil, false
	}
	return dict.refs[dict.starts[i]:dict.starts[i+1]], true
}

// word returns a string pointing into the mapping (which is never unmapped).
func (dict *Dictionary) word(i uint32) string {
	b := dict.blob[dict.wordOffs[i]:dict.wordOffs[i+1]]
	return unsafe.String(unsafe.SliceData(b), len(b))
}

func (dict *Dictionary) bucketContains(refs []uint32, word string) bool {
	return slices.ContainsFunc(refs, func(r uint32) bool { return dict.word(r) == word })
}

func (dict *Dictionary) bucketWords(refs []uint32) []string {
	words := make([]string, len(refs))
	for i, r := range refs {
		words[i] = dict.word(r)
	}
	return words
}

type Index struct {
	path         string
	dictionaries map[string]*Dictionary
}

// The loaded index is immutable, so spellchecks need no locking. loadMutex only serializes loadIndex calls.
var (
	loadedIndex atomic.Pointer[Index]
	loadMutex   sync.Mutex
)

// loadIndex maps the index file. Loading the same path again is a no-op.
func loadIndex(path string) error {
	loadMutex.Lock()
	defer loadMutex.Unlock()
	if index := loadedIndex.Load(); index != nil && index.path == path {
		return nil
	}
	index, err := OpenIndex(path)
	if err != nil {
		return err
	}
	loadedIndex.Store(index)
	return nil
}

func GetDictionary(language string) (*Dictionary, error) {
	index := loadedIndex.Load()
	if index == nil {
		return nil, errors.New("dictionary index not loaded")
	}
	dictionary, ok := index.dictionaries[language]
	if !ok {
		return nil, fmt.Errorf("no dictionary for language %q in %s", language, index.path)
	}
	return dictionary, nil
}

func OpenIndex(path string) (*Index, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()
	stat, err := file.Stat()
	if err != nil {
		return nil, err
	}
	if stat.Size() < indexHeaderSize {
		return nil, fmt.Errorf("invalid dictionary index %s: too small", path)
	}
	data, err := syscall.Mmap(int(file.Fd()), 0, int(stat.Size()), syscall.PROT_READ, syscall.MAP_SHARED)
	if err != nil {
		return nil, fmt.Errorf("mmap %s: %w", path, err)
	}
	// start reading the file into the page cache in the background, so that the first spellchecks don't block on I/O
	_ = syscall.Madvise(data, syscall.MADV_WILLNEED)

	index, err := parseIndex(data)
	if err != nil {
		_ = syscall.Munmap(data)
		return nil, fmt.Errorf("invalid dictionary index %s: %w", path, err)
	}
	index.path = path
	return index, nil
}

func parseIndex(data []byte) (*Index, error) {
	if [8]byte(data[:8]) != indexMagic {
		return nil, errors.New("wrong magic/version")
	}
	n := binary.LittleEndian.Uint64(data[8:])
	if n > uint64(len(data)-indexHeaderSize)/indexEntrySize {
		return nil, errors.New("truncated language table")
	}
	index := &Index{dictionaries: make(map[string]*Dictionary, n)}
	for i := range int(n) {
		entry := data[indexHeaderSize+i*indexEntrySize:]
		name := string(bytes.TrimRight(entry[:indexMaxNameLen], "\x00"))
		offset := binary.LittleEndian.Uint64(entry[indexMaxNameLen:])
		size := binary.LittleEndian.Uint64(entry[indexMaxNameLen+8:])
		if offset%8 != 0 || offset > uint64(len(data)) || size > uint64(len(data))-offset {
			return nil, fmt.Errorf("section %q out of bounds", name)
		}
		dictionary, err := parseSection(data[offset : offset+size])
		if err != nil {
			return nil, fmt.Errorf("section %q: %w", name, err)
		}
		index.dictionaries[name] = dictionary
	}
	return index, nil
}

// parseSection creates slices pointing directly into the mapping (assumes a little endian machine).
func parseSection(data []byte) (*Dictionary, error) {
	if len(data) < sectionHeaderSize {
		return nil, errors.New("truncated header")
	}
	var counts [4]uint64 // nKeys, nRefs, nWords, blobLen
	for i := range counts {
		counts[i] = binary.LittleEndian.Uint64(data[8*i:])
		if counts[i] > uint64(len(data)) {
			return nil, errors.New("truncated section")
		}
	}
	nKeys, nRefs, nWords, blobLen := int(counts[0]), int(counts[1]), int(counts[2]), int(counts[3])
	if sectionHeaderSize+8*nKeys+4*(nKeys+1)+4*nRefs+4*(nWords+1)+blobLen != len(data) {
		return nil, errors.New("section size mismatch")
	}
	off := sectionHeaderSize
	u64 := func(n int) []uint64 {
		s := unsafe.Slice((*uint64)(unsafe.Pointer(unsafe.SliceData(data[off:]))), n)
		off += 8 * n
		return s
	}
	u32 := func(n int) []uint32 {
		s := unsafe.Slice((*uint32)(unsafe.Pointer(unsafe.SliceData(data[off:]))), n)
		off += 4 * n
		return s
	}
	dictionary := &Dictionary{}
	dictionary.keys = u64(nKeys)
	dictionary.starts = u32(nKeys + 1)
	dictionary.refs = u32(nRefs)
	dictionary.wordOffs = u32(nWords + 1)
	dictionary.blob = data[off : off+blobLen]
	return dictionary, nil
}

// BuildIndex hashes all <language>.txt dictionaries in langDir and writes the index to indexPath.
// Returns the languages in the index.
func BuildIndex(langDir, indexPath string) ([]string, error) {
	files, err := filepath.Glob(filepath.Join(langDir, "*.txt"))
	if err != nil {
		return nil, err
	}
	if len(files) == 0 {
		return nil, fmt.Errorf("no dictionaries (*.txt) in %s", langDir)
	}
	slices.Sort(files)
	languages := make([]string, len(files))
	sections := make([][]byte, len(files))
	errs := make([]error, len(files))
	var wg sync.WaitGroup
	for i, file := range files {
		languages[i] = strings.TrimSuffix(filepath.Base(file), ".txt")
		if len(languages[i]) > indexMaxNameLen {
			return nil, fmt.Errorf("language name %q too long", languages[i])
		}
		wg.Go(func() {
			sections[i], errs[i] = buildSection(file)
		})
	}
	wg.Wait()
	if err := errors.Join(errs...); err != nil {
		return nil, err
	}

	var buf bytes.Buffer
	buf.Write(indexMagic[:])
	buf.Write(binary.LittleEndian.AppendUint64(nil, uint64(len(sections))))
	offset := uint64(indexHeaderSize + indexEntrySize*len(sections))
	for i, section := range sections {
		var name [indexMaxNameLen]byte
		copy(name[:], languages[i])
		buf.Write(name[:])
		buf.Write(binary.LittleEndian.AppendUint64(nil, offset))
		buf.Write(binary.LittleEndian.AppendUint64(nil, uint64(len(section))))
		offset += uint64(len(section)+7) &^ 7
	}
	for _, section := range sections {
		buf.Write(section)
		buf.Write(make([]byte, (8-len(section)%8)%8))
	}

	// atomic replace, a running process might have the old index mapped
	tmp := indexPath + ".tmp"
	if err := os.WriteFile(tmp, buf.Bytes(), 0o644); err != nil {
		return nil, err
	}
	return languages, os.Rename(tmp, indexPath)
}

// buildSection layout:
//
//	header:   nKeys, nRefs, nWords, blobLen uint64
//	keys:     [nKeys]uint64
//	starts:   [nKeys+1]uint32
//	refs:     [nRefs]uint32
//	wordOffs: [nWords+1]uint32
//	blob:     [blobLen]byte
func buildSection(txtPath string) ([]byte, error) {
	file, err := os.Open(txtPath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	type entry struct {
		hash uint64
		word uint32
	}
	var entries []entry
	var words []string
	wordIndex := make(map[string]uint32)
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		word := strings.TrimSpace(scanner.Text())
		if len(word) <= 1 {
			continue
		}
		i, ok := wordIndex[word]
		if !ok {
			i = uint32(len(words))
			words = append(words, word)
			wordIndex[word] = i
		}
		for _, hash := range HashWordAll(word) {
			if hash > 0 {
				entries = append(entries, entry{hash, i})
			}
		}
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	// sort by hash to group the buckets, deduplicate words within a bucket
	slices.SortFunc(entries, func(a, b entry) int {
		return cmp.Or(cmp.Compare(a.hash, b.hash), cmp.Compare(a.word, b.word))
	})
	entries = slices.Compact(entries)

	var keys []uint64
	var starts []uint32
	refs := make([]uint32, len(entries))
	for i, e := range entries {
		if i == 0 || e.hash != entries[i-1].hash {
			keys = append(keys, e.hash)
			starts = append(starts, uint32(i))
		}
		refs[i] = e.word
	}
	starts = append(starts, uint32(len(entries)))
	wordOffs := make([]uint32, 0, len(words)+1)
	var blob []byte
	for _, word := range words {
		wordOffs = append(wordOffs, uint32(len(blob)))
		blob = append(blob, word...)
	}
	wordOffs = append(wordOffs, uint32(len(blob)))
	if len(entries) > math.MaxUint32 || len(blob) > math.MaxUint32 {
		return nil, fmt.Errorf("%s: dictionary too large for the index format", txtPath)
	}

	out := make([]byte, 0, sectionHeaderSize+8*len(keys)+4*(len(starts)+len(refs)+len(wordOffs))+len(blob))
	for _, count := range []int{len(keys), len(refs), len(words), len(blob)} {
		out = binary.LittleEndian.AppendUint64(out, uint64(count))
	}
	for _, key := range keys {
		out = binary.LittleEndian.AppendUint64(out, key)
	}
	for _, values := range [][]uint32{starts, refs, wordOffs} {
		for _, v := range values {
			out = binary.LittleEndian.AppendUint32(out, v)
		}
	}
	return append(out, blob...), nil
}
