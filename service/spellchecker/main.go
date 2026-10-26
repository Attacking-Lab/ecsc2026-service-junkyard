package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"path/filepath"
)

var FileDir = "../gateway/data/files/"
var LangDir = "../language-tool/languages"

func initGlobals() {
	if envPath := os.Getenv("FILE_DIR"); envPath != "" {
		FileDir = envPath
	}
	if envPath := os.Getenv("LANG_DIR"); envPath != "" {
		LangDir = envPath
	}
}

func isPermitted(filename string, metadata string, username string) bool {
	meta, err := os.ReadFile(filepath.Join(FileDir, filename, metadata+".meta"))
	if err != nil {
		return false
	}
	owner, public, err := ParseMetaOwnerPublic(meta)
	return err == nil && (owner == username || public)
}

func genericHandler(w http.ResponseWriter, r *http.Request) (string, map[string]any) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return "", nil
	}

	// Extract query parameters
	filename := r.URL.Query().Get("filename")
	username := r.URL.Query().Get("username")
	metadata := r.URL.Query().Get("meta")
	if !isPermitted(filename, metadata, username) {
		http.Error(w, "Forbidden/Invalid file/meta", http.StatusForbidden)
		return "", nil
	}

	// Read JSON body
	var userdata map[string]any
	decoder := json.NewDecoder(r.Body)
	if err := decoder.Decode(&userdata); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return "", nil
	}

	return filename, userdata
}

func spellcheckerHandler(w http.ResponseWriter, r *http.Request) {
	filename, userdata := genericHandler(w, r)
	if userdata == nil {
		return
	}

	// Call EstimateLanguage with the filename and JSON body
	language, confidence, err := EstimateLanguage(filepath.Join(filename, "data.txt"), userdata)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Spellcheck to response
	content, err := os.ReadFile(filepath.Join(FileDir, filename, "data.txt"))
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	response, err := Spellcheck(string(content), language, confidence)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	_, _ = w.Write([]byte(response))
}

func readHandler(w http.ResponseWriter, r *http.Request) {
	filename, userdata := genericHandler(w, r)
	if userdata == nil {
		return
	}

	content, err := os.ReadFile(filepath.Join(FileDir, filename, "data.txt"))
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	_, _ = w.Write(content)
}

func main() {
	initGlobals()

	http.HandleFunc("/spellchecker/process", spellcheckerHandler)
	http.HandleFunc("/reader/process", readHandler)

	log.Println("Starting server on :9303")
	if err := http.ListenAndServe(":9303", nil); err != nil {
		log.Fatal(err)
	}
}
