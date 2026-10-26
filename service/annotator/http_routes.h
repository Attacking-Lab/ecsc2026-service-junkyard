#ifndef ANNOTATOR_HTTP_ROUTES_H
#define ANNOTATOR_HTTP_ROUTES_H

struct evhttp_request;
struct evhttp_uri;
struct evbuffer;

struct ToolParams {
    const char* username;
    const char* filename;
    const char* metadata;
};

struct ToolResult {
    int success;
    char* uuid;
    const char* error_message;
};

int route_censor(struct evhttp_request* req, struct evhttp_uri* path, struct evbuffer* evb);

int route_cropper(struct evhttp_request* req, struct evhttp_uri* path, struct evbuffer* evb);

#endif //ANNOTATOR_HTTP_ROUTES_H
