# Technical Notes

## MCP Tool Result Capture Limitation (2025-11-04)

### Issue
We attempted to programmatically capture MCP tool results (event data from `mcp__google-calendar__create-event`) to format output directly instead of parsing Claude's markdown responses.

### Investigation Summary

**Approaches Tried:**
1. **ToolResultBlock in message stream** - Expected `ToolResultBlock` to appear in `client.receive_response()` alongside `TextBlock` and `ToolUseBlock`
2. **PostToolUse hooks** - Configured `hooks={'PostToolUse': [HookMatcher(...)]}` in `ClaudeAgentOptions`

**Findings:**
- `ToolResultBlock` is **never present** in the message stream for MCP tools
- The Claude Agent SDK executes MCP tools internally and only exposes Claude's final text response
- PostToolUse hooks do **not fire** for MCP tool executions (tested with debug logging)
- The message stream only contains:
  - `ToolUseBlock` - when Claude calls a tool
  - `TextBlock` - Claude's final text response

### Current Architecture

**What Works:**
- **Tests pass** - We mock `ToolResultBlock` in unit tests to simulate ideal scenario
- **Formatter ready** - `format_tool_results()` works perfectly when tool results are available
- **Fallback works** - `format_event_response()` parses Claude's markdown (production mode)
- **URL truncation fixed** - Full URLs now display correctly in both formatters

**Code Structure:**
```python
# agent.py - process_events() returns dict
return {
    "text": "".join(response_text),
    "tool_results": self.captured_tool_results,  # Empty in production
}

# agent.py - create_events() prioritizes tool results
if isinstance(result, dict):
    if result.get("tool_results"):
        format_tool_results(result["tool_results"], console)  # Tests only
    else:
        format_event_response(result["text"], console)  # Production
```

### Why This Design Is Still Correct

1. **Future-proof** - If SDK exposes tool results later, we're ready
2. **Testable** - Mocking tool results gives us high-quality unit tests
3. **Robust fallback** - Markdown parsing works in production
4. **Clean architecture** - Separation of concerns between data sources

### Potential Future Solutions

**If SDK adds support:**
- Tool result access via message stream (`ToolResultBlock`)
- Working PostToolUse hooks with proper signatures
- Alternative API like `client.get_tool_results()`

**Alternative approach (not recommended):**
- Parse Claude's text response (current fallback)
- Instruct Claude to output structured JSON (fragile, wastes tokens)
- Build custom MCP client (complex, reinvents SDK)

### References

**Code locations:**
- Tool result capture: `gcallm/agent.py:166` (`captured_tool_results`)
- Tool result formatter: `gcallm/formatter.py:30` (`format_tool_results`)
- Fallback formatter: `gcallm/formatter.py:88` (`format_event_response`)
- CLI integration: `gcallm/agent.py:468` (`create_events`)

**Test coverage:**
- `tests/test_formatter.py::TestToolResultFormatter` - Direct tool result formatting
- `tests/test_cli.py::test_cli_uses_tool_results_when_available` - CLI integration
- `tests/test_agent.py::test_agent_captures_and_returns_tool_results` - Agent capture

### Commits

- `d139508` - Phase 1: Agent captures tool results
- `04e144d` - Phase 2: Formatter for tool results
- `2de74e5` - Phase 3: CLI integration and refactor

### Conclusion

**Production behavior:** CLI uses markdown parsing (fallback) because `tool_results` is always empty.

**Test behavior:** Unit tests mock tool results to verify formatting logic works correctly.

**Architecture:** Clean separation allows us to switch to tool results seamlessly if SDK adds support.
