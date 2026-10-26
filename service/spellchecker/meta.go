package main

import (
	"errors"
)

func ParseMetaOwnerPublic(data []byte) (string, bool, error) {
	owner := ""
	public := false

	offset := 0
	for offset < len(data) {
		if offset >= len(data) {
			break
		}

		recordType := data[offset]
		offset++

		switch recordType {
		case 0x01:
			if offset >= len(data) {
				return "", false, errors.New("invalid meta file: owner length missing")
			}
			length := int(data[offset])
			offset++

			if offset+length > len(data) {
				return "", false, errors.New("invalid meta file: owner string truncated")
			}
			owner = string(data[offset : offset+length])
			offset += length

		case 0x02:
			public = true

		case 0x03:
			offset += 8

		case 0x04:
			offset += 8

		default:
			return "", false, errors.New("invalid meta file: unknown record type")
		}
	}

	return owner, public, nil
}
