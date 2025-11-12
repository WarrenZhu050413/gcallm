# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`gcallm` is a CLI tool that uses Claude (via the Agent SDK) to add events to Google Calendar in natural language. It connects to the Google Calendar API through the `@cocal/google-calendar-mcp` MCP server.

**Key architecture pattern**: Explicit MCP configuration is done in code (gcallm/agent.py:86-90), not through external config files. The MCP server path and credentials are configured programmatically.

## Development Commands

### Setup
```bash
# Install in development mode (editable)
make dev

# Install in production mode
make install

# First-time setup: configure OAuth credentials
gcallm setup ~/path/to/gcp-oauth.keys.json

# Authenticate the MCP server
export GOOGLE_OAUTH_CREDENTIALS="/path/to/gcp-oauth.keys.json"
npx @cocal/google-calendar-mcp auth
```

### Testing
```bash
# Run all tests (145 tests total)
make test

# Run specific test file
pytest tests/test_cli.py -v

# Run with coverage
pytest tests/ --cov=gcallm --cov-report=term-missing

# Run specific test markers
pytest tests/ -m unit     # Unit tests only
pytest tests/ -m slow     # Slow tests only
```

### Code Quality
```bash
make format    # Format with black
make lint      # Lint with ruff
```

### Building
```bash
make build     # Build package for PyPI
make publish   # Publish to PyPI (requires credentials)
make clean     # Remove build artifacts
```

## Architecture

### Core Components

1. **gcallm/cli.py** - Command-line interface using Typer
   - Main entry point intercepts unknown commands and treats them as event descriptions
   - Handles multiple input modes: direct args, stdin, clipboard, editor, **screenshots**
   - Default command behavior: `gcallm "text"` → creates events without explicit subcommand
   - Screenshot flags: `--screenshot` / `-s` (latest 1), `--screenshots N` (latest N)

2. **gcallm/agent.py** - Claude Agent SDK integration
   - `CalendarAgent` class wraps Claude SDK with Google Calendar MCP access
   - `SYSTEM_PROMPT` (line 23) defines Claude's behavior - can be customized via `gcallm prompt`
   - MCP configuration is explicit: uses `McpStdioServerConfig` with npx command
   - OAuth credentials loaded from config and injected via environment variable
   - **Screenshot support**: `add_dirs=[~/Desktop]` grants filesystem access when screenshots provided

3. **gcallm/config.py** - Configuration management
   - Stores OAuth credentials path and custom system prompt in `~/.config/gcallm/config.json`
   - Auto-detects OAuth credentials in default locations:
     1. `~/.gmail-mcp/gcp-oauth.keys.json` (shared with gmail-mcp)
     2. `~/.config/gcallm/gcp-oauth.keys.json`
     3. `~/gcp-oauth.keys.json`

4. **gcallm/helpers/input.py** - Input handling (consolidated from 3 previous files)
   - Priority order: direct input → **screenshots** → stdin → clipboard → editor
   - Editor mode opens `$EDITOR` (default: vim) when no input provided
   - Composable handlers: each returns None when not applicable

5. **gcallm/helpers/screenshot.py** - Screenshot discovery
   - `find_recent_screenshots(count, directory)` discovers latest N screenshots from ~/Desktop
   - Sorts by modification time (newest first)
   - Returns absolute paths for Claude to read via Read tool
   - No user configuration required

6. **gcallm/formatter.py** - Rich output formatting
   - `parse_xml_events()` parses Claude's XML-formatted event responses
   - Handles URL escaping (& → &amp;) for Google Calendar URLs
   - Displays events with Rich Panel/Table components
   - `display_conflict_report()` shows interactive mode conflicts

7. **gcallm/conflicts.py** - Interactive mode conflict detection
   - `ConflictReport` dataclass with `is_important` logic
   - Two-phase workflow: analysis → user decision → creation

### Input Flow
```
User Input (text / screenshot / clipboard / stdin / editor)
    ↓
CLI (gcallm/cli.py)
    ├─ Screenshot discovery (gcallm/helpers/screenshot.py) if --screenshot/-s
    └─ Input Handler (helpers/input.py)
    ↓
Agent (gcallm/agent.py)
    ├─ Configure add_dirs=[~/Desktop] if screenshots
    └─ Pass screenshot paths in prompt
    ↓
Claude SDK → Google Calendar MCP → Google Calendar API
              ↓ (if screenshots)
              Read tool (Desktop access via add_dirs)
    ↓
Formatter (formatter.py) → Rich Console
```

### Configuration Flow
- OAuth credentials: `config.json` → env var → MCP server
- Custom system prompt: `config.json` → agent initialization
- **Screenshot access**: Programmatic via `add_dirs` (zero user config)

### Screenshot Feature Architecture

The screenshot feature was implemented following strict TDD (Red-Green-Refactor):

**Key Design Decisions:**
1. **Zero Configuration**: Uses `ClaudeAgentOptions.add_dirs=[~/Desktop]` for programmatic filesystem access
   - No MCP server setup required
   - No user configuration files
   - Automatically granted when `screenshot_paths` provided

2. **Discovery Pattern**: `find_recent_screenshots()` in `gcallm/helpers/screenshot.py`
   - Searches `~/Desktop` for `Screenshot*.png` files
   - Sorts by modification time (newest first)
   - Returns absolute paths for Claude's Read tool

3. **Integration Points**:
   - **CLI**: `--screenshot` / `-s` flags trigger screenshot discovery before input handling
   - **Agent**: Receives `screenshot_paths`, configures `add_dirs`, includes paths in prompt
   - **System Prompt**: Instructions for Claude to analyze screenshots for event details

4. **Testing Strategy** (11 tests):
   - `test_screenshot.py`: Discovery, CLI integration, agent integration
   - Mocking pattern: Patch `gcallm.cli.create_events` (where imported, not where defined)

### XML Event Format

Claude returns events in XML format for reliable parsing:

```xml
<events>
  <event>
    <title>Event Title</title>
    <when>Nov 12, 2024 at 4:30 PM - 6:00 PM</when>
    <link>https://www.google.com/calendar/event?eid=...</link>
  </event>
</events>
```

**Implementation details:**
- `parse_xml_events()` uses ElementTree with URL escaping
- Handles unescaped `&` in Google Calendar URLs by replacing in `<link>` tags only
- Falls back to markdown display if XML parsing fails

### Interactive Mode: Two-Phase Workflow

When `--interactive` / `-i` flag is used:

1. **Phase 1 - Analysis**:
   - `process_events_interactive()` calls Claude to analyze events
   - Claude checks calendar for conflicts
   - Returns `ConflictReport` with `is_important` flag

2. **Conflict Detection**:
   - **Important**: 2+ overlapping events, all-day events, >50% overlap
   - **Minor**: Single event, <50% overlap, tentative events

3. **User Decision**:
   - Important conflicts → prompt user to confirm
   - Minor/no conflicts → proceed automatically

4. **Phase 2 - Creation**:
   - If user confirms, call Claude again to create events
   - Display formatted results

**Key files:**
- `gcallm/conflicts.py`: `ConflictReport` dataclass, XML parsing
- `gcallm/agent.py`: `process_events_interactive()`, `ask_question()`
- `gcallm/formatter.py`: `display_conflict_report()`

## Testing Philosophy

This project follows TDD (Test-Driven Development). All features have comprehensive test coverage:
- **CLI tests** (test_cli.py) - Command routing, input handling, Rich formatting
- **Agent tests** (test_agent.py) - Claude SDK integration, config loading
- **Formatter tests** (test_formatter.py) - Rich output formatting, event parsing, URL display
- **Input tests** (test_input_sources.py) - Stdin, clipboard, editor modes
- **Screenshot tests** (test_screenshot.py) - Screenshot discovery, CLI flags, agent integration
- **Interactive tests** (test_interactive.py) - Conflict detection, two-phase workflow
- **XML parsing tests** (test_xml_event_parsing.py) - XML parsing with URL escaping

When adding new features:
1. Write tests first (RED phase)
2. Implement the feature (GREEN phase)
3. Refactor and cleanup (REFACTOR phase)
4. Ensure all tests pass: `make test` (145/145 tests passing)

## Important Notes

### OAuth Credentials Auto-Discovery
The tool automatically looks for OAuth credentials in multiple locations. Users don't need to run `gcallm setup` if their credentials are in one of the default locations.

### MCP Configuration Pattern
Unlike tools that use external MCP config files, `gcallm` configures the MCP server directly in code using `McpStdioServerConfig`. This makes the tool self-contained and easier to distribute.

### Custom System Prompts
Users can customize how Claude interprets events via `gcallm prompt`. The custom prompt is stored in config and takes precedence over the default `SYSTEM_PROMPT`.

### Default Command Behavior
The CLI intercepts unknown commands and treats them as event descriptions. This means `gcallm "Meeting tomorrow"` works without needing `gcallm add "Meeting tomorrow"`.

### Composable Input Handler Pattern
Input handlers in `gcallm/helpers/input.py` follow a consistent pattern:
- Each handler takes its specific parameters plus `console: Console`
- Returns `None` if not applicable, allowing next handler to try
- This enables clean priority ordering without nested conditionals

Example:
```python
def handle_screenshot_input(screenshots: Optional[int], console: Console) -> Optional[list[str]]:
    if screenshots is None:
        return None
    # ... implementation
    return screenshot_paths
```

## Dependencies

- **typer[all]** - CLI framework with Rich support
- **rich** - Terminal formatting and output
- **claude-agent-sdk** - Claude Agent SDK for MCP integration
- **python-dateutil** - Date/time parsing utilities
- **Node.js 16+** - Required for the Google Calendar MCP server (npx)

## Common Issues

### "Calendar tools not available"
The MCP server isn't authenticated. Run:
```bash
export GOOGLE_OAUTH_CREDENTIALS="/path/to/gcp-oauth.keys.json"
npx @cocal/google-calendar-mcp auth
```

### Tokens expired (after 7 days)
Google OAuth tokens expire weekly when the app is in test mode. Re-authenticate:
```bash
npx @cocal/google-calendar-mcp auth
```

## Recent Improvements

### Consolidated Input Handling
The input handling was refactored from 3 separate files into a single organized module (`gcallm/helpers/input.py`) with clear sections:
1. InputContext dataclass
2. Low-level functions (stdin, clipboard, editor)
3. Composable handlers (screenshot, direct, stdin, clipboard, editor)
4. Legacy compatibility function

### Simplified Screenshot Flags
- Single screenshot: `-s` flag (boolean)
- Multiple screenshots: `--screenshots N` flag (integer)
- Combined in CLI: `screenshot_count = 1 if screenshot else screenshots`
- Design decision made due to typer/click limitations with optional flag values

### Structured XML Event Display
- Replaced fragile markdown parsing with robust XML parsing
- System prompt updated to request XML format
- URL escaping handles `&` in Google Calendar URLs
- Falls back to markdown if XML parsing fails

### General-Purpose Ask Command
- New `gcallm ask "question"` command for calendar questions
- Replaced redundant `status` command
- Simplified `calendars` command to use ask internally
