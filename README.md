# gcallm: Google Calendar w/ Claude

Simple CLI to use Claude to add events to gcal in natural language. It has been helpful for me to quickly add events from the terminal without opening the calendar UI and specifying everything manually!

```bash
$ gcallm "Coffee with Sarah tomorrow at 2pm"
✅ Created 1 event:
Coffee with Sarah
- Date & Time: Tomorrow at 2:00 PM - 3:00 PM
- Calendar: primary
```

## Installation

### Prerequisites

1. **Python 3.10+**
2. **Node.js 16+** (for the Google Calendar MCP server)
3. **Google Cloud OAuth credentials** (see [Setup](#setup) below)

### Option 1: Install from PyPI (Recommended)

```bash
pip install gcallm
```

### Option 2: Install from Source

**For regular use:**
```bash
# Clone the repository
git clone https://github.com/WarrenZhu050413/gcallm.git
cd gcallm

# Install with make (requires uv)
make install
```

**For development:**
```bash
# Clone the repository
git clone https://github.com/WarrenZhu050413/gcallm.git
cd gcallm

# Install in editable mode
make dev
```

> **Note**: `uv` is a fast Python package installer. Install it with: `pip install uv` or see [uv docs](https://docs.astral.sh/uv/)

## Setup

### 1. Get Google OAuth Credentials

> **Note**: The credential setup instructions below are adapted from the [@cocal/google-calendar-mcp](https://github.com/nspady/google-calendar-mcp) repository.

1. **Go to [Google Cloud Console](https://console.cloud.google.com)**
   - Create a new project or select an existing one
   - Ensure the correct project is selected from the top bar

2. **Enable Calendar API**
   - Navigate to APIs & Services → Library
   - Search for "Google Calendar API"
   - Click "Enable"

3. **Create OAuth Credentials**
   - Go to APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Configure consent screen if prompted:
     - Choose "User data" as the data access type
     - Provide app name and your contact email
     - Add scopes:
       - `https://www.googleapis.com/auth/calendar.events`
       - `https://www.googleapis.com/auth/calendar`
   - **Application type**: Select "Desktop app"
   - Click "Create" and download the JSON file
   - Save it somewhere safe (e.g., `~/gcp-oauth.keys.json`)

4. **Add Test User** (if app is in test mode)
   - Go to OAuth consent screen → Test users
   - Add your email address as a test user
   - Note: Changes may take a few minutes to propagate

### 2. Configure OAuth Credentials

Save your OAuth credentials file to a permanent location (e.g., `~/gcp-oauth.keys.json`), then run:

```bash
gcallm setup ~/gcp-oauth.keys.json
```

This saves the path so `gcallm` automatically uses it. You only need to do this once!

### 3. Authenticate the MCP Server

```bash
# Set the credentials path (gcallm setup does this automatically, but you can also set it manually)
export GOOGLE_OAUTH_CREDENTIALS="/path/to/your/gcp-oauth.keys.json"

# Run authentication
npx @cocal/google-calendar-mcp auth
```

This will:
- Open your browser for Google OAuth
- Request calendar permissions
- Save authentication tokens to `~/.config/google-calendar-mcp/tokens.json`

**Note about "test mode"**: If your Google Cloud app is in test mode (the default), refresh tokens expire after 7 days for security. You'll need to re-run `npx @cocal/google-calendar-mcp auth` weekly. For personal use, this is fine! To avoid this, publish your app in Google Cloud Console.

### 4. Verify Setup

```bash
gcallm verify
```

You should see:
```
✓ Google Calendar MCP: Working
✓ Claude Agent SDK: Working
✅ All checks passed!
```

## Usage

### Quick Start

```bash
# Natural language
gcallm "Coffee with Sarah tomorrow at 2pm at Blue Bottle"

# From URL (automatically fetched)
gcallm "https://www.aiandsoul.org/..."

# From screenshot (most powerful!)
gcallm --screenshot        # Latest screenshot from Desktop
gcallm -s                  # Short form
gcallm --screenshots 3     # Latest 3 screenshots

# From clipboard
gcallm --clipboard
gcallm -c

# From stdin (pipe support)
pbpaste | gcallm
cat events.txt | gcallm
echo "Meeting tomorrow at 3pm" | gcallm

# No args = open editor
gcallm
# Opens $EDITOR, you write events, save & quit
```

### Screenshot-Based Event Creation

**One of gcallm's most powerful features** is creating events directly from screenshots of flyers, emails, meeting invites, or any image containing event information.

```bash
# Basic usage
gcallm add --screenshot           # Use most recent screenshot
gcallm add -s                     # Short form

# Multiple screenshots
gcallm add --screenshots 3        # Use latest 3 screenshots

# Screenshot + additional context
gcallm add -s "CS50 team meeting"
```

**How it works:**
1. Take a screenshot (⌘+Shift+4 on macOS) of event information
2. Run `gcallm add --screenshot`
3. Claude analyzes the screenshot and extracts event details
4. Event is automatically created in your calendar

**No setup required** - Desktop access is configured automatically.

**Examples:**
- **Event flyer** → Claude extracts date, time, location, description
- **Email invitation** → Claude creates calendar event with all details
- **Meeting notes** → Claude schedules follow-up meetings
- **Existing calendar** → Claude replicates events to your calendar

### Interactive Mode: Conflict Detection

Want `gcallm` to check for scheduling conflicts before creating events? Use interactive mode!

```bash
# Interactive mode - checks for conflicts first
gcallm --interactive "Team meeting tomorrow at 2pm"
gcallm -i "Coffee with Sarah Friday at 10am"

# Works with all input methods
gcallm add -i --screenshot
gcallm -i --clipboard
pbpaste | gcallm -i
```

**How it works:**

1. **Phase 1 - Analysis**: Claude analyzes the event and checks your calendar for conflicts
2. **Conflict Detection**: Distinguishes between important and minor conflicts:
   - **Important conflicts**: 2+ overlapping events, all-day events, significant overlap (>50%)
   - **Minor conflicts**: Single event with minor overlap (<50%), tentative events
3. **User Decision**: You decide whether to proceed if important conflicts are found
4. **Phase 2 - Creation**: Event is created based on your decision

**Example interactive flow:**

```bash
$ gcallm -i "Workshop tomorrow 2-5pm"

⚠️ Scheduling Conflicts Detected

Proposed event:
- Workshop
- Date & Time: Tomorrow at 2:00 PM - 5:00 PM

Conflicts detected:
- Meeting A (2:00 PM - 3:00 PM)
- Meeting B (3:00 PM - 4:00 PM)
- Meeting C (4:00 PM - 5:00 PM)

Do you want to create this event anyway? [y/N]: n

Event creation cancelled.
```

**When to use interactive mode:**
- Busy schedule with many meetings
- Important events that shouldn't conflict
- Want to review before committing
- Checking availability for proposed times

**When to skip it:**
- Quick, informal events
- You know your schedule is clear
- Lower-stakes calendar entries

### Commands

```bash
# Setup & Configuration
gcallm setup ~/gcp-oauth.keys.json  # Configure OAuth credentials path
gcallm prompt                        # Customize system prompt in editor
gcallm prompt --reset                # Reset to default system prompt

# Calendar Operations
gcallm verify      # Verify setup
gcallm status      # Show calendar status
gcallm calendars   # List available calendars
gcallm --help      # Show help
```


## Configuration

### OAuth Credentials

`gcallm` automatically looks for OAuth credentials in these locations (in order):

1. **Configured path** (via `gcallm setup`)
2. **Default locations** (if no config):
   - `~/.gmail-mcp/gcp-oauth.keys.json` (shared with gmail-mcp)
   - `~/.config/gcallm/gcp-oauth.keys.json`
   - `~/gcp-oauth.keys.json`

**No configuration needed** if your OAuth file is in one of these default locations! Just download your credentials from Google Cloud Console and save them to `~/.gmail-mcp/gcp-oauth.keys.json`.

To use a custom location:
```bash
gcallm setup /path/to/your/gcp-oauth.keys.json
```

This saves the path to `~/.config/gcallm/config.json` so you never have to set `GOOGLE_OAUTH_CREDENTIALS` manually!

### Custom System Prompt

Want to customize how Claude interprets your events? Use `gcallm prompt` to edit the system prompt:

```bash
gcallm prompt  # Opens editor with current prompt
```

Example customizations:
- Change default meeting duration
- Add specific instructions for handling certain event types
- Customize output format
- Add domain-specific terminology

To revert to the default: `gcallm prompt --reset`

## How It Works

`gcallm` uses the [Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk/) to interact with Claude, which has direct access to your Google Calendar via the [@cocal/google-calendar-mcp](https://github.com/nspady/google-calendar-mcp) server.

```
┌─────────────┐
│   gcallm    │  Natural language input
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Claude    │  Parses intent, dates, details
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Google Cal  │  Creates events via MCP
│  MCP Server │
└─────────────┘
```

**Key features:**
1. **Explicit MCP configuration** - MCP server is configured directly in code, no external config files needed
2. **Natural language parsing** - Claude handles all the complexity of date/time interpretation
3. **Direct API access** - MCP server talks directly to Google Calendar API

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/WarrenZhu050413/gcallm.git
cd gcallm

# Install in development mode (editable)
make dev

# Verify installation
gcallm verify
```

### Available Commands

```bash
make dev       # Install in development mode (editable)
make install   # Install in production mode (non-editable)
make test      # Run tests
make format    # Format code with black
make lint      # Lint code with ruff
make build     # Build package for PyPI
make clean     # Remove build artifacts
make uninstall # Uninstall gcallm
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_cli.py -v

# Run with coverage
pytest tests/ --cov=gcallm --cov-report=term-missing
```

### Test-Driven Development

This project follows TDD (Test-Driven Development). All features have tests:
- **114 tests total** - 100% passing
- **CLI tests** - Command routing, input handling, Rich formatting
- **Agent tests** - Claude SDK integration, config loading
- **Formatter tests** - Rich output formatting, event parsing
- **Input tests** - Stdin, clipboard, editor modes
- **Screenshot tests** - Screenshot discovery, CLI integration, agent integration
- **Interactive tests** - Conflict detection, user interaction, two-phase workflow

### Code Quality

```bash
make format   # Format with black
make lint     # Lint with ruff
```

### Building for PyPI

```bash
# Build distribution packages
make build

# Publish to PyPI (requires PyPI credentials)
make publish
```

## Troubleshooting

### "Calendar tools not available"

The MCP server isn't authenticated. Run:
```bash
export GOOGLE_OAUTH_CREDENTIALS="/path/to/your/gcp-oauth.keys.json"
npx @cocal/google-calendar-mcp auth
```

### Tokens expired (after 7 days)

In test mode, OAuth tokens expire weekly. Re-run the auth command:
```bash
npx @cocal/google-calendar-mcp auth
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow TDD - write tests first!
4. Ensure all tests pass (`make test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Acknowledgments

- **OAuth Setup**: Credential setup instructions adapted from [@cocal/google-calendar-mcp](https://github.com/nspady/google-calendar-mcp)
- **Inspiration**: This project was inspired by [gmaillm](https://github.com/grll/gmaillm) - a similar CLI for Gmail operations

## License

MIT License - see [LICENSE](LICENSE) file for details

## Author

Created by Warren Zhu ([@WarrenZhu050413](https://github.com/WarrenZhu050413))
