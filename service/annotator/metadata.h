#ifndef ANNOTATOR_METADATA_H
#define ANNOTATOR_METADATA_H

#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "utils.h"


#define INVALID 0xffff


enum MetaType {
    OWNER = 1,
    PUBLIC = 2,
    CROP = 3,
    CENSOR = 4,
};


typedef struct {
    uint8_t type;

    union {
        struct {
            unsigned char len;
            char username[0];
        } owner;

        struct {
            int16_t t;
            int16_t r;
            int16_t b;
            int16_t l;
        } crop;

        struct {
            int16_t x;
            int16_t y;
            int16_t w;
            int16_t h;
        } censor;
    };
} __attribute__((packed)) MetadataEntry;


static size_t metadata_entry_len(MetadataEntry* entry) {
    switch (entry->type) {
    case OWNER:
        return 2 + entry->owner.len;
    case PUBLIC:
        return 1;
    case CROP:
        return 1 + sizeof(entry->crop);
    case CENSOR:
        return 1 + sizeof(entry->censor);
    default:
        return INVALID;
    }
}

static MetadataEntry* next_metadata_entry(Buffer* buffer, MetadataEntry* last_entry) {
    size_t offset = last_entry ? (((char*)last_entry) - buffer->data) + metadata_entry_len(last_entry) : 0;
    if (offset >= INVALID || offset + 1 >= buffer->len) {
        return 0;
    }
    MetadataEntry* entry = (MetadataEntry*)(buffer->data + offset);
    size_t entry_len = metadata_entry_len(entry);
    if (offset + entry_len > buffer->len || entry_len >= INVALID) {
        return 0;
    }
    return entry;
}

static void append_metadata_entry(Buffer* buffer, MetadataEntry* entry) {
    size_t len = metadata_entry_len(entry);
    if (len >= INVALID) {
        free_buffer(buffer);
        return;
    }
    char* data = realloc(buffer->data, buffer->len + len);
    if (!data) {
        free_buffer(buffer);
        return;
    }
    buffer->data = data;
    memcpy(buffer->data + buffer->len, entry, len);
    buffer->len += len;
}

#endif //ANNOTATOR_METADATA_H
