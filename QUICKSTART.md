# gcallm Quick Start

## ✅ Installation Complete!

Your `gcallm` CLI is now installed and ready to use.

## 🧪 Test It

### 1. Verify Setup
```bash
gcallm verify
```

### 2. Try Creating an Event

**Simple event:**
```bash
gcallm "Coffee with Alice tomorrow at 2pm"
```

**From URL (your original example):**
```bash
gcallm "https://www.aiandsoul.org/..."
```

**From clipboard:**
```bash
# Copy some event text, then:
gcallm --clipboard
# or
gcallm -c
```

**From stdin:**
```bash
pbpaste | gcallm
echo "Meeting tomorrow at 3pm" | gcallm
cat events.txt | gcallm
```

**Editor mode:**
```bash
gcallm
# Opens $EDITOR, write your events, save & quit
```

## 📖 All Commands

```bash
gcallm [event description]    # Create events
gcallm verify                 # Verify setup
gcallm status                 # Show calendar status
gcallm calendars              # List calendars
gcallm --help                 # Show help
```

## 🎯 What Happens

1. You provide event description
2. Claude gets current date/time
3. Claude fetches URLs if needed
4. Claude creates events directly via GCal MCP
5. Shows you what was created

## 🔧 Troubleshooting

**If verify fails:**
```bash
# Check MCP is installed
claude mcp list | grep calendar

# Should see:
# google-calendar: npx @cocal/google-calendar-mcp - ✓ Connected
```

**If events aren't created:**
- Make sure you're authenticated with Google Calendar
- Check: `gcallm status`

## 💡 Examples

```bash
# Single event
gcallm "Dentist appointment next Tuesday at 3pm"

# Multiple events
echo "Team standup Monday, Wednesday, Friday at 9am" | gcallm

# Recurring event
gcallm "Weekly 1:1 with manager every Thursday at 2pm for 4 weeks"

# From URL with all details
gcallm "https://eventbrite.com/event/..."
```

## 🎨 Features

- ✅ Natural language parsing
- ✅ URL fetching and extraction
- ✅ Multiple input modes (args, stdin, clipboard, editor)
- ✅ Automatic date resolution ("tomorrow", "next week")
- ✅ Duration inference (meetings = 1hr, calls = 30min)
- ✅ Multiple events from single input
- ✅ Beautiful Rich output
- ✅ No confirmation needed (low stakes)

## 📝 Notes

- Uses Sonnet model for good date parsing
- Calendar operations are low-stakes (easy to delete/modify)
- Always shows what's being sent to Claude (transparency)
- Post-creation summary instead of pre-confirmation

---

Ready to test! Try: `gcallm "Test event tomorrow at 3pm"`
