#define _GNU_SOURCE
#include <stdlib.h>
#include <string.h>
#include <uuid/uuid.h>
#include <event2/http.h>
#include "metadata.h"
#include "tools.h"


const char* BASEPATH = 0;


__attribute__((constructor))
static void init_basepath() {
    BASEPATH = getenv("FILE_DIR");
    if (!BASEPATH) {
        BASEPATH = "../../gateway/data/files";
    }
}


static char* gen_uuid() {
    uuid_t binuuid;
    uuid_generate_random(binuuid);
    char* uuid = malloc(64);
    uuid_unparse_lower(binuuid, uuid);
    return uuid;
}


static int16_t to_int(const char* str) {
    if (!str) return -1;
    const long result = strtol(str, NULL, 10);
    if (result < 0 || result > 4096) return -1;
    return (int16_t)result;
}


static int16_t max(const int16_t a, const int16_t b) {
    return a > b ? a : b;
}


const struct ToolResult internal_error = {
    .success = 0,
    .uuid = 0,
    .error_message = "internal error",
};


static int read_owned_file(struct ToolParams* params, Buffer* meta_buffer) {
    // Original meta filename
    char* meta_filename;
    if (asprintf(&meta_filename, "%s/%s/%s.meta", BASEPATH, params->filename, params->metadata) == -1) {
        return 1;
    }

    // Read it
    *meta_buffer = read_file(meta_filename);
    free(meta_filename);
    if (meta_buffer->data == NULL || meta_buffer->len == 0) {
        free_buffer(meta_buffer);
        return 2;
    }

    // Process it / permission checks
    MetadataEntry* entry = NULL;
    while ((entry = next_metadata_entry(meta_buffer, entry))) {
        if (entry->type == OWNER) {
            if (strncmp(params->username, entry->owner.username, entry->owner.len) != 0) {
                free_buffer(meta_buffer);
                return 3;
            }
        }
    }

    // All ok
    return 0;
}


static struct ToolResult write_result_meta(const char* filename, Buffer* meta_buffer) {
    // Write back
    char* uuid = gen_uuid();
    char* meta_filename;
    if (asprintf(&meta_filename, "%s/%s/%s.meta", BASEPATH, filename, uuid) == -1) {
        free_buffer(meta_buffer);
        free(uuid);
        return internal_error;
    }
    write_file(meta_filename, meta_buffer);
    free(meta_filename);

    // Done!
    free_buffer(meta_buffer);
    return (struct ToolResult){
        .success = 1,
        .uuid = uuid,
        .error_message = 0,
    };
}


struct ToolResult tool_censor(struct ToolParams* params, struct evkeyvalq* query) {
    // Parse parameters
    int16_t x = to_int(evhttp_find_header(query, "x"));
    int16_t y = to_int(evhttp_find_header(query, "y"));
    int16_t w = to_int(evhttp_find_header(query, "w"));
    int16_t h = to_int(evhttp_find_header(query, "h"));
    if (x < 0 || y < 0 || w < 0 || h < 0) {
        return internal_error;
    }

    // Read metadata file and check ownership
    Buffer meta_buffer = {0};
    if (read_owned_file(params, &meta_buffer) != 0) {
        free_buffer(&meta_buffer);
        return (struct ToolResult){
            .success = 0,
            .uuid = 0,
            .error_message = "cannot read metadata",
        };
    }

    // Append
    MetadataEntry new_entry = {
        .type = CENSOR,
        .censor = {
            .x = x,
            .y = y,
            .w = w,
            .h = h,
        }
    };
    append_metadata_entry(&meta_buffer, &new_entry);

    // Write back
    return write_result_meta(params->filename, &meta_buffer);
}


struct ToolResult tool_cropper(struct ToolParams* params, struct evkeyvalq* query) {
    // Parse parameters
    int16_t t = to_int(evhttp_find_header(query, "t"));
    int16_t r = to_int(evhttp_find_header(query, "r"));
    int16_t b = to_int(evhttp_find_header(query, "b"));
    int16_t l = to_int(evhttp_find_header(query, "l"));
    if (t < 0 || r < 0 || b < 0 || l < 0) {
        return internal_error;
    }

    // Read metadata file and check ownership
    Buffer meta_buffer;
    if (read_owned_file(params, &meta_buffer) != 0) {
        free_buffer(&meta_buffer);
        return (struct ToolResult){
            .success = 0,
            .uuid = 0,
            .error_message = "cannot read metadata",
        };
    }

    // Adjust existing censor blocks (censor applied after cropping)
    MetadataEntry* entry = NULL;
    while ((entry = next_metadata_entry(&meta_buffer, entry))) {
        if (entry->type == CENSOR) {
            entry->censor.x -= l;
            if (entry->censor.x < 0) {
                entry->censor.w = max(0, entry->censor.w + entry->censor.x);
                entry->censor.x = 0;
            }
            entry->censor.y -= t;
            if (entry->censor.y < 0) {
                entry->censor.h = max(0, entry->censor.h + entry->censor.y);
                entry->censor.y = 0;
            }
        }
    }

    // Append
    MetadataEntry new_entry = {
        .type = CROP,
        .crop = {
            .t = t,
            .r = r,
            .b = b,
            .l = l,
        }
    };
    append_metadata_entry(&meta_buffer, &new_entry);

    // Write back
    return write_result_meta(params->filename, &meta_buffer);
}
