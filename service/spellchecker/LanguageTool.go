package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"maps"
	"net/http"
)

const LanguageToolUrl = "http://language-tool/cgi-bin/language-tool"

func EstimateLanguage(filename string, userdata map[string]interface{}) (language string, confidence float64, err error) {
	jsonRequestDict := map[string]interface{}{"file": filename}
	maps.Insert(jsonRequestDict, maps.All(userdata))
	jsonRequest, _ := json.Marshal(jsonRequestDict)

	resp, err := http.Post(LanguageToolUrl, "text/json", bytes.NewBuffer(jsonRequest))
	if err != nil {
		return "", 0, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return "", 0, fmt.Errorf("language tool returned unexpected status code: %d", resp.StatusCode)
	}

	var result map[string]interface{}
	decoder := json.NewDecoder(resp.Body)
	if err := decoder.Decode(&result); err != nil {
		return "", 0, err
	}

	langValue, ok := result["language"]
	if !ok {
		return "", 0, fmt.Errorf("language field not found in response")
	}

	language, ok = langValue.(string)
	if !ok {
		return "", 0, fmt.Errorf("language field is not a string")
	}

	confValue, ok := result["confidence"]
	if !ok {
		return "", 0, fmt.Errorf("confidence field not found in response")
	}

	confidence, ok = confValue.(float64)
	if !ok {
		return "", 0, fmt.Errorf("confidence field is not a float64")
	}

	return language, confidence, nil
}
