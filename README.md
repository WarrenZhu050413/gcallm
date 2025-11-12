# gcallm: Google Calendar w/ Claude

gcallm is a simple CLI that uses Claude to add events to Google Calendar in natural language. It supports text input, screenshots, clipboard. It also supports interactive workflows where you use a text editor to input the gcal information, as well as asking the user for confirmation if it finds significant conflict. I found it useful. I hope you do too!

## Quickstart

```bash
$ gcallm "Coffee with Sarah tomorrow at 2pm"
✅ Created event:
Coffee with Sarah
- Date & Time: Tomorrow at 2:00 PM - 3:00 PM
- Calendar: primary
```

- **Direct input** - `gcallm "Meeting tomorrow"`
- **Screenshots** - `gcallm -s`
- **Clipboard** - `gcallm -c`
- **Stdin** - `pbpaste | gcallm`
- **Editor** - `gcallm` (opens $EDITOR)
- **URL** - `gcallm "https://example.com/event"`


## Installation

### Option 1: Install from PyPI (Recommended)

**Using pip:**
```bash
pip install gcallm
```

**Using uv (faster):**
```bash
uv tool install gcallm
```

### Option 2: Install from Source

```bash
git clone https://github.com/WarrenZhu050413/gcallm.git
cd gcallm
make install
```

**For development:**
```bash
make dev    # Install in editable mode
```

## Quick Start

### 1. Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Enable Google Calendar API
3. Create OAuth credentials (Desktop app)
4. Download the JSON file and save it (e.g., `~/gcp-oauth.keys.json`)

**Detailed instructions:** See [docs/oauth.md](docs/oauth.md)

### 2. Configure OAuth Credentials

```bash
gcallm setup ~/gcp-oauth.keys.json
```

### 3. Authenticate

```bash
export GOOGLE_OAUTH_CREDENTIALS="$HOME/gcp-oauth.keys.json"
npx @cocal/google-calendar-mcp auth
```

This opens your browser to grant calendar permissions.

### 4. Verify Setup

```bash
gcallm verify
```

Expected output:
```
✓ Google Calendar MCP: Working
✓ Claude Agent SDK: Working
✅ All checks passed!
```

### 5. Add Your First Event

```bash
gcallm "Test event tomorrow at 3pm"
```

## Usage

```bash
# Natural language
gcallm "Coffee with Sarah tomorrow at 2pm"

# From screenshot
gcallm -s                    # Latest screenshot
gcallm --screenshots 3       # Latest 3 screenshots

# From clipboard
gcallm -c

# From stdin
pbpaste | gcallm
cat events.txt | gcallm

# Interactive mode (check conflicts)
gcallm -i "Meeting tomorrow at 2pm"

# Ask questions
gcallm ask "What's on my calendar today?"

# No args = open editor
gcallm
```

**Full documentation:** See [docs/cli.md](docs/cli.md)

## Documentation

- **[CLI Usage Guide](docs/cli.md)** - Complete command reference and usage examples
- **[OAuth Setup](docs/oauth.md)** - Detailed OAuth configuration instructions
- **[CLAUDE.md](CLAUDE.md)** - Developer documentation for contributing

## Key Features Explained

### Screenshot Support

Take a screenshot of an event flyer, email, or calendar, then run:

```bash
gcallm -s
```

Claude analyzes the screenshot and creates the event automatically. No manual typing needed!

### Interactive Mode

Check for scheduling conflicts before creating events:

```bash
gcallm -i "Workshop tomorrow 2-5pm"
```

Claude checks your calendar and warns you about conflicts, letting you decide whether to proceed.

## Prerequisites

- **Python 3.10+**
- **Node.js 16+** (for Google Calendar MCP server)
- **Google OAuth credentials** (see [Quick Start](#quick-start))

## Troubleshooting

### "Calendar tools not available"

The MCP server isn't authenticated. Run:
```bash
export GOOGLE_OAUTH_CREDENTIALS="/path/to/gcp-oauth.keys.json"
npx @cocal/google-calendar-mcp auth
```

### Tokens expired (after 7 days)

If your Google Cloud app is in test mode, tokens expire weekly:
```bash
npx @cocal/google-calendar-mcp auth
```

**Full troubleshooting:** See [docs/oauth.md](docs/oauth.md#troubleshooting)

## Development

```bash
make dev       # Install in development mode
make test      # Run tests (145 tests)
make format    # Format code
make lint      # Lint code
make build     # Build for PyPI
```

**Developer documentation:** See [CLAUDE.md](CLAUDE.md)

## How It Works

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

- **Claude Agent SDK** - Natural language understanding
- **Google Calendar MCP** - Direct API access
- **Explicit MCP config** - No external config files needed

## Contributing

Contributions welcome! This project follows TDD (Test-Driven Development).

1. Fork the repository
2. Create a feature branch
3. Write tests first (Red-Green-Refactor)
4. Ensure all tests pass (`make test`)
5. Submit a Pull Request

See [CLAUDE.md](CLAUDE.md) for architecture details.

## Acknowledgments

- **OAuth Setup**: Instructions adapted from [@cocal/google-calendar-mcp](https://github.com/nspady/google-calendar-mcp)
- **Coding Agent**: Uses [Claude Code](https://github.com/anthropics/claude-code)
- **Agent Development Environment**: Uses [orchestra](https://github.com/fulcrumresearch/orchestra)

## License

MIT License - see [LICENSE](LICENSE) file for details

## Author

Created by Warren Zhu ([@WarrenZhu050413](https://www.warrenzhu.com/))
