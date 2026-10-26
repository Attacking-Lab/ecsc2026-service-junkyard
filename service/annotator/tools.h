#ifndef ANNOTATOR_TOOLS_H
#define ANNOTATOR_TOOLS_H

#include "http_routes.h"

struct evkeyvalq;

struct ToolResult tool_censor(struct ToolParams* params, struct evkeyvalq* query);

struct ToolResult tool_cropper(struct ToolParams* params, struct evkeyvalq* query);

#endif //ANNOTATOR_TOOLS_H
