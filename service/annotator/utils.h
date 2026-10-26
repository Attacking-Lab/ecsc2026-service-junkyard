#ifndef ANNOTATOR_UTILS_H
#define ANNOTATOR_UTILS_H

typedef struct {
    char* data;
    size_t len;
} Buffer;


static void free_buffer(Buffer* buffer) {
    if (buffer->data) {
        free(buffer->data);
        buffer->data = NULL;
    }
    buffer->len = 0;
}


static Buffer read_file(const char* path) {
    Buffer buffer = {0};
    FILE* file = fopen(path, "rb");
    if (!file) {
        return buffer;
    }

    fseek(file, 0, SEEK_END);
    buffer.len = ftell(file);
    fseek(file, 0, SEEK_SET);
    if (buffer.len > 20000) {
        fclose(file);
        return buffer;
    }

    buffer.data = malloc(buffer.len);
    if (!buffer.data) {
        fclose(file);
        return buffer;
    }

    size_t read_size = fread(buffer.data, 1, buffer.len, file);
    fclose(file);

    if (read_size != buffer.len) {
        free(buffer.data);
        buffer.data = NULL;
        return buffer;
    }

    return buffer;
}


static void write_file(const char* path, const Buffer* buffer) {
    FILE* file = fopen(path, "wb");
    if (!file) {
        return;
    }
    fwrite(buffer->data, 1, buffer->len, file);
    fclose(file);
}


#endif //ANNOTATOR_UTILS_H
