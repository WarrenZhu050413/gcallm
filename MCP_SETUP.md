# Google Calendar MCP Setup

`gcallm` uses the Google Calendar MCP server to interact with your calendar. The MCP server is **explicitly configured in the code** and requires one-time authentication.

## Quick Setup

### 1. Authenticate the MCP Server

Run the authentication flow for the Google Calendar MCP server:

```bash
npx @cocal/google-calendar-mcp auth
```

This will:
- Prompt you to log in to your Google account
- Request calendar permissions
- Save authentication credentials locally

### 2. Test the Tool

After authentication, test `gcallm`:

```bash
echo "Test meeting tomorrow at 3pm" | gcallm
```

## How It Works

`gcallm` explicitly configures the Google Calendar MCP server in code:

```python
google_calendar_mcp: McpStdioServerConfig = {
    "command": "npx",
    "args": ["-y", "@cocal/google-calendar-mcp"],
}
```

**No external configuration files needed!** The MCP server is configured programmatically.

## Troubleshooting

### "Invalid MCP configuration" Error

This error is **FIXED** in the current version. The MCP server is now correctly configured using TypedDict syntax.

### "gcalcli requires authentication"

If you see this error, it means the Google Calendar MCP server isn't authenticated. Run:

```bash
npx @cocal/google-calendar-mcp auth
```

### MCP Server Not Found

If the server isn't being detected, ensure you have Node.js and npx installed:

```bash
node --version  # Should be v16 or higher
npx --version
```

## What Gets Created

The MCP server will:
- ✅ Access your Google Calendar
- ✅ Get current date/time
- ✅ Create events
- ✅ List calendars
- ✅ Check free/busy times

**No manual calendar setup needed** - everything is handled by the MCP server!

## Security Notes

- Authentication credentials are stored locally by the MCP server
- The MCP server runs locally on your machine
- No credentials are sent to third parties
- You can revoke access anytime via Google Account settings

## Alternative: Using Different MCP Servers

If you want to use a different Google Calendar MCP implementation, modify the configuration in `gcallm/agent.py`:

```python
google_calendar_mcp: McpStdioServerConfig = {
    "command": "your-command",
    "args": ["your", "args"],
}
```
