# CLI Usage Guide

This guide covers all `gcallm` commands and usage patterns.

## Quick Reference

```bash
gcallm "Meeting tomorrow at 3pm"    # Add event with natural language
gcallm -s                            # Add event from screenshot
gcallm -c                            # Add event from clipboard
gcallm -i "Workshop Friday"          # Interactive mode (check conflicts)
gcallm ask "What's on my calendar?"  # Ask questions
gcallm verify                        # Verify setup
```

## Installation

See [README.md](../README.md) for installation instructions.

## Commands

### `gcallm add` - Add Events

Add events to Google Calendar using natural language or screenshots.

```bash
# Natural language (most common)
gcallm "Coffee with Sarah tomorrow at 2pm"
gcallm "Team meeting Friday 10am-11am at Building 10"

# From URL (automatically fetched)
gcallm "https://www.aiandsoul.org/..."

# From screenshot
gcallm -s                    # Latest screenshot
gcallm --screenshots 3       # Latest 3 screenshots

# From clipboard
gcallm -c
gcallm --clipboard

# From stdin (pipe support)
pbpaste | gcallm
cat events.txt | gcallm
echo "Meeting tomorrow at 3pm" | gcallm

# No args = open editor
gcallm
# Opens $EDITOR, you write events, save & quit
```

**Note:** The `add` command is the default, so `gcallm "text"` is equivalent to `gcallm add "text"`.

#### Interactive Mode (`-i` / `--interactive`)

Interactive mode checks your calendar for conflicts before creating events:

```bash
gcallm -i "Workshop tomorrow 2-5pm"
gcallm --interactive "Coffee meeting Friday at 10am"

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

**Example flow:**

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

#### Screenshot-Based Event Creation

One of gcallm's most powerful features is creating events directly from screenshots:

```bash
# Basic usage
gcallm -s                     # Use most recent screenshot
gcallm add -s                 # Explicit command

# Multiple screenshots
gcallm --screenshots 3        # Use latest 3 screenshots

# Screenshot + additional context
gcallm -s "CS50 team meeting"
```

**How it works:**
1. Take a screenshot (⌘+Shift+4 on macOS) of event information
2. Run `gcallm -s`
3. Claude analyzes the screenshot and extracts event details
4. Event is automatically created in your calendar

**No setup required** - Desktop access is configured automatically.

**Examples:**
- **Event flyer** → Claude extracts date, time, location, description
- **Email invitation** → Claude creates calendar event with all details
- **Meeting notes** → Claude schedules follow-up meetings
- **Existing calendar** → Claude replicates events to your calendar

#### Options

- `--clipboard` / `-c` - Read from clipboard (uses `pbpaste`)
- `-s` - Use latest screenshot from Desktop
- `--screenshots N` - Use N latest screenshots from Desktop
- `--interactive` / `-i` - Check for conflicts before creating events
- `--calendar TEXT` - Target calendar (default: `primary`)
- `--output-format [rich|json]` - Output format (default: `rich`)

### `gcallm ask` - Ask Questions

Ask Claude questions about your Google Calendar:

```bash
gcallm ask "What meetings do I have today?"
gcallm ask "Am I free tomorrow afternoon?"
gcallm ask "What's on my calendar this week?"
gcallm ask "When is my next meeting with Sarah?"
```

Claude has direct access to your calendar via the MCP server and can answer any question about your events, availability, and schedule.

### `gcallm calendars` - List Calendars

List all available calendars:

```bash
gcallm calendars
```

This is a convenience alias for `gcallm ask "List my calendars"`.

### `gcallm verify` - Verify Setup

Verify that Google Calendar MCP is properly configured:

```bash
gcallm verify
```

Expected output:
```
✓ Google Calendar MCP: Working
✓ Claude Agent SDK: Working
✅ All checks passed!
```

If verification fails, see [OAuth Setup](oauth.md) for troubleshooting.

### `gcallm setup` - Configure OAuth

Configure the path to your OAuth credentials file:

```bash
gcallm setup ~/path/to/gcp-oauth.keys.json
```

This saves the path to `~/.config/gcallm/config.json` so you never have to set `GOOGLE_OAUTH_CREDENTIALS` manually.

**Note:** `gcallm` automatically looks for OAuth credentials in these default locations:
1. `~/.gmail-mcp/gcp-oauth.keys.json` (shared with gmail-mcp)
2. `~/.config/gcallm/gcp-oauth.keys.json`
3. `~/gcp-oauth.keys.json`

If your credentials are in one of these locations, you don't need to run `gcallm setup`.

See [OAuth Setup](oauth.md) for detailed instructions on obtaining credentials.

### `gcallm config` - Configure Settings

Configure gcallm settings like model and custom system prompt:

```bash
# Edit system prompt
gcallm config prompt

# Reset to default prompt
gcallm config prompt --reset
```

**Custom system prompts** allow you to customize how Claude interprets your events:
- Change default meeting duration
- Add specific instructions for handling certain event types
- Customize output format
- Add domain-specific terminology

The custom prompt is stored in `~/.config/gcallm/config.json` and takes precedence over the default system prompt.

## Input Modes

`gcallm` supports multiple input modes with the following priority:

1. **Direct input** - Command line argument
2. **Screenshots** - `--screenshot` / `-s` or `--screenshots N`
3. **Stdin** - Piped input
4. **Clipboard** - `--clipboard` / `-c`
5. **Editor** - Opens `$EDITOR` if no input provided

## Output Formats

### Rich Format (Default)

Formatted, colored output using Rich library:

```bash
gcallm "Meeting tomorrow at 3pm"
```

Output:
```
┌─ ✅ Event Created Successfully ─────────────────┐
│ Event:    Coffee with Sarah                     │
│ When:     Tomorrow at 2:00 PM - 3:00 PM        │
│ Link:     https://www.google.com/calendar/...  │
└─────────────────────────────────────────────────┘
```

### JSON Format

Machine-readable JSON output:

```bash
gcallm "Meeting tomorrow" --output-format json
```

## Tips & Tricks

### Natural Language Flexibility

Claude understands many natural language patterns:

```bash
gcallm "Coffee with Sarah tomorrow at 2pm at Blue Bottle"
gcallm "Team standup every Monday at 9am"
gcallm "Workshop next Friday 2-5pm"
gcallm "Lunch with team on 12/25 at noon"
gcallm "Call with client in 2 hours"
```

### URL Fetching

Pass a URL and Claude will fetch and parse it for event details:

```bash
gcallm "https://www.example.com/event-page"
```

### Piping from Other Commands

Combine with other CLI tools:

```bash
# From clipboard
pbpaste | gcallm

# From file
cat events.txt | gcallm

# From curl
curl https://example.com/events.txt | gcallm
```

### Editor Mode

If you have a long event description or multiple events, use editor mode:

```bash
gcallm
# Opens $EDITOR (vim, nano, etc.)
# Write your events, save & quit
```

### Multiple Events at Once

Claude can create multiple events from a single input:

```bash
gcallm "Team meeting Monday at 10am, one-on-one with Sarah Tuesday at 2pm, workshop Friday 3-5pm"
```

Or use editor mode for better formatting.

## Troubleshooting

### "Calendar tools not available"

The MCP server isn't authenticated. See [OAuth Setup](oauth.md) for authentication instructions.

### Tokens expired (after 7 days)

If your Google Cloud app is in test mode, OAuth tokens expire weekly. Re-authenticate:

```bash
npx @cocal/google-calendar-mcp auth
```

For permanent access, publish your app in Google Cloud Console.

### "No input provided"

You need to provide input via one of these methods:
- Direct argument: `gcallm "text"`
- Screenshot: `gcallm -s`
- Clipboard: `gcallm -c`
- Stdin: `echo "text" | gcallm`
- Editor: `gcallm` (opens editor)

### Events not appearing in calendar

1. Check that you're using the correct calendar: `gcallm calendars`
2. Specify calendar explicitly: `gcallm "Event" --calendar "Work"`
3. Verify MCP setup: `gcallm verify`

## See Also

- [OAuth Setup Guide](oauth.md) - Detailed instructions for obtaining and configuring OAuth credentials
- [README.md](../README.md) - Installation and quickstart
- [CLAUDE.md](../CLAUDE.md) - Developer documentation for contributing
