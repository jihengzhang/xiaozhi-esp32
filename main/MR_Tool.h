#ifndef MR_TOOL_H
#define MR_TOOL_H

#include "mcp_server.h"

// A simple wrapper class for MR-only tools.
// It marks the underlying McpTool instance as MR-only on construction.
class MRTool : public McpTool {
public:
    MRTool(const std::string& name,
           const std::string& description,
           const PropertyList& properties,
           std::function<ReturnValue(const PropertyList&)> callback)
        : McpTool(name, description, properties, callback) {
        set_mr_only(true);
    }
};

#endif // MR_TOOL_H
