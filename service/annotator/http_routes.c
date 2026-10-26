#include <stdlib.h>
#include <string.h>

#include <event2/buffer.h>
#include <event2/event.h>
#include <event2/http.h>
#include <event2/keyvalq_struct.h>

#include "http_routes.h"
#include "tools.h"


typedef struct ToolResult (*tool_func)(struct ToolParams*, struct evkeyvalq*);

static int tool_route(tool_func tool, struct evhttp_request* req, struct evhttp_uri* path, struct evbuffer* evb) {
    struct evkeyvalq query_parameters;
    if (evhttp_parse_query_str(evhttp_uri_get_query(path), &query_parameters)) {
        evhttp_send_error(req, HTTP_INTERNAL, "cannot parse query string");
        return 0;
    }

    struct ToolParams params;
    params.username = evhttp_find_header(&query_parameters, "username");
    params.filename = evhttp_find_header(&query_parameters, "filename");
    params.metadata = evhttp_find_header(&query_parameters, "meta");
    if (!params.username || !params.filename || !params.metadata) {
        evhttp_send_error(req, HTTP_BADREQUEST, "required query params missing");
        evhttp_clear_headers(&query_parameters);
        return 0;
    }

    const struct ToolResult result = tool(&params, &query_parameters);

    if (!result.success || !result.uuid) {
        evhttp_send_error(req, HTTP_BADREQUEST, result.error_message);
        evhttp_clear_headers(&query_parameters);
        if (result.uuid) {
            free(result.uuid);
        }
        return 0;
    }

    evbuffer_add_printf(evb, "\"%s\"", result.uuid);
    free(result.uuid);
    evhttp_clear_headers(&query_parameters);
    return 1;
}


int route_censor(struct evhttp_request* req, struct evhttp_uri* path, struct evbuffer* evb) {
    return tool_route(tool_censor, req, path, evb);
}


int route_cropper(struct evhttp_request* req, struct evhttp_uri* path, struct evbuffer* evb) {
    return tool_route(tool_cropper, req, path, evb);
}
