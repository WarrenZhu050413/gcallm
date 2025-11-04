# gcallm - Google Calendar + LLM

A simple, beautiful CLI that uses Claude to add events to Google Calendar using natural language.

```bash
$ gcallm "Coffee with Sarah tomorrow at 2pm"
✅ Created 1 event:
Coffee with Sarah
- Date & Time: Tomorrow at 2:00 PM - 3:00 PM
- Calendar: primary
```

## Features

- 🎯 **Simple**: Just describe your event in natural language
- 🔗 **Smart URLs**: Automatically fetches and parses event pages
- 📋 **Flexible Input**: Args, stdin, clipboard, or editor
- 🎨 **Beautiful Output**: Color-coded, easy to scan
- ⚡ **Fast**: Creates events immediately, no confirmation needed
- 🤖 **Intelligent**: Claude handles date parsing and ambiguity

## Installation

### Prerequisites

1. **Python 3.10+** and **uv** ([installation guide](https://docs.astral.sh/uv/))
2. **Node.js 16+** (for the Google Calendar MCP server)
3. **Google Cloud OAuth credentials** (see [Setup](#setup) below)

### Install gcallm

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/gcallm.git
cd gcallm

# Install with uv
uv tool install --editable .
```

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

### 2. Authenticate the MCP Server

```bash
# Set the credentials path
export GOOGLE_OAUTH_CREDENTIALS="/path/to/your/gcp-oauth.keys.json"

# Run authentication
npx @cocal/google-calendar-mcp auth
```

This will:
- Open your browser for Google OAuth
- Request calendar permissions
- Save authentication tokens locally

**Note**: In test mode, tokens expire after 7 days. Re-run the auth command to refresh.

### 3. Verify Setup

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

### Commands

```bash
gcallm verify      # Verify setup
gcallm status      # Show calendar status
gcallm calendars   # List available calendars
```

## Features

- 🎯 **Simple**: Just describe your event in natural language
- 🔗 **Smart URLs**: Automatically fetches and parses event pages
- 📋 **Flexible Input**: Args, stdin, clipboard, or editor
- 🎨 **Beautiful Output**: Color-coded, easy to scan
- ⚡ **Fast**: Creates events immediately, no confirmation needed
- 🤖 **Intelligent**: Claude handles date parsing and ambiguity

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
- **24 tests total** - 100% passing
- **CLI tests** - Command routing, input handling
- **Agent tests** - Claude SDK integration
- **Input tests** - Stdin, clipboard, editor modes

### Code Quality

```bash
make format   # Format with black
make lint     # Lint with ruff
```

## Troubleshooting

### "Invalid MCP configuration" Error

This has been fixed in the current version. If you see this, make sure you're on the latest commit.

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

Created by Warren Zhu ([@YOUR_GITHUB](https://github.com/YOUR_GITHUB))
