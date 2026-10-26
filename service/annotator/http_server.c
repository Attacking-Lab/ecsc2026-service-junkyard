#include <stdlib.h>
#include <signal.h>
#include <string.h>
#include <event2/buffer.h>
#include <event2/event.h>
#include <event2/http.h>

#include "http_routes.h"


static void add_content_length(struct evhttp_request* req, unsigned len) {
    char buf[128];
    snprintf(buf, sizeof(buf), "%u", len);
    evhttp_add_header(evhttp_request_get_output_headers(req), "Content-Length", buf);
}


static void request_handler(struct evhttp_request* req, void* arg) {
    const enum evhttp_cmd_type cmd = evhttp_request_get_command(req);
    struct evbuffer* evb = NULL;

    /* Decode the URI */
    struct evhttp_uri* decoded = evhttp_uri_parse(evhttp_request_get_uri(req));
    if (!decoded) {
        evhttp_send_error(req, HTTP_BADREQUEST, 0);
        return;
    }

    const char* path = evhttp_uri_get_path(decoded);
    if (!path) {
        evhttp_send_error(req, HTTP_INTERNAL, 0);
        goto cleanup;
    }

    if ((evb = evbuffer_new()) == NULL) {
        evhttp_send_error(req, HTTP_INTERNAL, 0);
        goto cleanup;
    }

    if (cmd == EVHTTP_REQ_POST && strcmp(path, "/tool/censor/process") == 0) {
        if (route_censor(req, decoded, evb)) {
            add_content_length(req, evbuffer_get_length(evb));
            evhttp_add_header(evhttp_request_get_output_headers(req), "Content-Type", "application/json");
            evhttp_send_reply(req, HTTP_OK, "OK", evb);
        }
    }
    else if (cmd == EVHTTP_REQ_POST && strcmp(path, "/tool/cropper/process") == 0) {
        if (route_cropper(req, decoded, evb)) {
            add_content_length(req, evbuffer_get_length(evb));
            evhttp_add_header(evhttp_request_get_output_headers(req), "Content-Type", "application/json");
            evhttp_send_reply(req, HTTP_OK, "OK", evb);
        }
    }
    else {
        evhttp_send_error(req, HTTP_NOTFOUND, "not found");
    }

cleanup:
    evhttp_uri_free(decoded);
    if (evb) {
        evbuffer_free(evb);
    }
}


static void signal_cb(evutil_socket_t fd, short event, void* arg) {
    fputs("signal received, terminating\n", stderr);
    event_base_loopbreak(arg);
}

int main() {
    // adapted from https://libevent.org/libevent-book/Ref10_http_server.html
    ev_uint16_t http_port = 9302;
    const char* http_addr = "0.0.0.0";

    struct event_base* base = event_base_new();
    if (!base) abort();

    struct evhttp* http_server = evhttp_new(base);
    if (!http_server) abort();
    if (evhttp_bind_socket(http_server, http_addr, http_port)) abort();
    evhttp_set_gencb(http_server, request_handler, NULL);

    struct event* sig_int = evsignal_new(base, SIGINT, signal_cb, base);
    struct event* sig_term = evsignal_new(base, SIGTERM, signal_cb, base);
    event_add(sig_int, NULL);
    event_add(sig_term, NULL);

    fprintf(stderr, "Listening on http://%s:%d ...\n", http_addr, http_port);

    event_base_dispatch(base);

    evhttp_free(http_server);
    event_free(sig_int);
    event_free(sig_term);
    event_base_free(base);
}
