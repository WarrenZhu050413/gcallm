# gcallm - Google Calendar + LLM

A simple, beautiful CLI that uses Claude to add events to Google Calendar using natural language.

## Installation

```bash
# Install with uv
make install

# Or manually
uv tool install --editable .
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

## Requirements

- Python 3.10+
- Google Calendar MCP configured
- Claude Agent SDK

## Development

```bash
make dev      # Install in development mode
make test     # Run tests
make format   # Format code
make lint     # Lint code
```

## How It Works

1. You provide event description (text, URL, clipboard, or editor)
2. Claude uses Google Calendar MCP to create events directly
3. Shows what was created with beautiful formatting

No complex parsing, no confirmation prompts - just fast, intelligent event creation.
