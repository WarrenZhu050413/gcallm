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
# Run all tests (51 tests total)
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

4. **gcallm/helpers/input.py** - Input handling
   - Priority order: direct input → **screenshots** → stdin → clipboard → editor
   - Editor mode opens `$EDITOR` (default: vim) when no input provided

5. **gcallm/screenshot.py** - Screenshot discovery (NEW)
   - `find_recent_screenshots(count, directory)` discovers latest N screenshots from ~/Desktop
   - Sorts by modification time (newest first)
   - Returns absolute paths for Claude to read via Read tool
   - No user configuration required

6. **gcallm/formatter.py** - Rich output formatting
   - Parses Claude's event summaries and formats with Rich components
   - Handles error messages and warnings
   - Displays full URLs without truncation (clickable links)

### Input Flow
```
User Input (text / screenshot / clipboard / stdin / editor)
    ↓
CLI (gcallm/cli.py)
    ├─ Screenshot discovery (gcallm/screenshot.py) if --screenshot/-s
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

2. **Discovery Pattern**: `find_recent_screenshots()` in `gcallm/screenshot.py`
   - Searches `~/Desktop` for `Screenshot*.png` files
   - Sorts by modification time (newest first)
   - Returns absolute paths for Claude's Read tool

3. **Integration Points**:
   - **CLI**: `--screenshot` / `-s` flags trigger screenshot discovery before input handling
   - **Agent**: Receives `screenshot_paths`, configures `add_dirs`, includes paths in prompt
   - **System Prompt**: Instructions for Claude to analyze screenshots for event details

4. **Testing Strategy** (11 new tests, all passing):
   - `test_screenshot.py`: Discovery, CLI integration, agent integration
   - Mocking pattern: Patch `gcallm.cli.create_events` (where imported, not where defined)

## Testing Philosophy

This project follows TDD (Test-Driven Development). All features have comprehensive test coverage:
- **CLI tests** (test_cli.py) - Command routing, input handling, Rich formatting
- **Agent tests** (test_agent.py) - Claude SDK integration, config loading
- **Formatter tests** (test_formatter.py) - Rich output formatting, event parsing, URL display
- **Input tests** (test_input.py) - Stdin, clipboard, editor modes
- **Screenshot tests** (test_screenshot.py) - Screenshot discovery, CLI flags, agent integration

When adding new features:
1. Write tests first (RED phase)
2. Implement the feature (GREEN phase)
3. Refactor and cleanup (REFACTOR phase)
4. Ensure all tests pass: `make test` (51/51 tests passing)

## Important Notes

### OAuth Credentials Auto-Discovery
The tool automatically looks for OAuth credentials in multiple locations. Users don't need to run `gcallm setup` if their credentials are in one of the default locations.

### MCP Configuration Pattern
Unlike tools that use external MCP config files, `gcallm` configures the MCP server directly in code using `McpStdioServerConfig`. This makes the tool self-contained and easier to distribute.

### Custom System Prompts
Users can customize how Claude interprets events via `gcallm prompt`. The custom prompt is stored in config and takes precedence over the default `SYSTEM_PROMPT`.

### Default Command Behavior
The CLI intercepts unknown commands and treats them as event descriptions. This means `gcallm "Meeting tomorrow"` works without needing `gcallm add "Meeting tomorrow"`.

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
- Make install after adding a feature and having tested it.