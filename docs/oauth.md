# OAuth Setup Guide

This guide walks you through obtaining Google OAuth credentials and configuring `gcallm` to access your Google Calendar.

## Overview

`gcallm` uses OAuth 2.0 to access your Google Calendar via the `@cocal/google-calendar-mcp` MCP server. You'll need to:

1. Create OAuth credentials in Google Cloud Console
2. Configure the credentials path in `gcallm`
3. Authenticate the MCP server

## Prerequisites

- Google account
- Node.js 16+ (for the MCP server)

## Step 1: Get Google OAuth Credentials

> **Note**: These instructions are adapted from the [@cocal/google-calendar-mcp](https://github.com/nspady/google-calendar-mcp) repository.

### 1.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Ensure the correct project is selected from the top bar

### 1.2 Enable Calendar API

1. Navigate to **APIs & Services → Library**
2. Search for "**Google Calendar API**"
3. Click "**Enable**"

### 1.3 Create OAuth Credentials

1. Go to **APIs & Services → Credentials**
2. Click "**Create Credentials**" → "**OAuth client ID**"
3. Configure consent screen if prompted:
   - Choose "**User data**" as the data access type
   - Provide app name and your contact email
   - Add scopes:
     - `https://www.googleapis.com/auth/calendar.events`
     - `https://www.googleapis.com/auth/calendar`
4. **Application type**: Select "**Desktop app**"
5. Click "**Create**" and download the JSON file
6. Save it somewhere safe (e.g., `~/gcp-oauth.keys.json`)

### 1.4 Add Test User (if app is in test mode)

If your Google Cloud app is in test mode (the default):

1. Go to **OAuth consent screen → Test users**
2. Add your email address as a test user
3. Note: Changes may take a few minutes to propagate

**Important about test mode:**
- OAuth tokens expire after 7 days for security
- You'll need to re-authenticate weekly (see [Re-authentication](#re-authentication) below)
- For personal use, this is fine!
- To avoid this, publish your app in Google Cloud Console (requires verification)

## Step 2: Configure OAuth Credentials

Save your OAuth credentials file to a permanent location, then configure `gcallm`:

```bash
# Save credentials (recommended locations)
mv ~/Downloads/client_secret_*.json ~/gcp-oauth.keys.json

# Configure gcallm
gcallm setup ~/gcp-oauth.keys.json
```

This saves the path to `~/.config/gcallm/config.json` so `gcallm` automatically uses it.

### Auto-Discovery

`gcallm` automatically looks for OAuth credentials in these locations (in order):

1. **Configured path** (via `gcallm setup`)
2. **Default locations** (if no config):
   - `~/.gmail-mcp/gcp-oauth.keys.json` (shared with gmail-mcp)
   - `~/.config/gcallm/gcp-oauth.keys.json`
   - `~/gcp-oauth.keys.json`

**No configuration needed** if your OAuth file is in one of these default locations!

## Step 3: Authenticate the MCP Server

```bash
# Set the credentials path (gcallm setup does this automatically, but you can also set it manually)
export GOOGLE_OAUTH_CREDENTIALS="$HOME/gcp-oauth.keys.json"

# Run authentication
npx @cocal/google-calendar-mcp auth
```

This will:
1. Open your browser for Google OAuth
2. Request calendar permissions
3. Save authentication tokens to `~/.config/google-calendar-mcp/tokens.json`

Follow the prompts in your browser:
- Sign in with your Google account
- Grant calendar access permissions
- You'll see a "Authentication successful!" message

## Step 4: Verify Setup

```bash
gcallm verify
```

Expected output:
```
✓ Google Calendar MCP: Working
✓ Claude Agent SDK: Working
✅ All checks passed!
```

If you see this, you're all set! Try adding an event:

```bash
gcallm "Test event tomorrow at 3pm"
```

## Troubleshooting

### "Calendar tools not available"

**Problem:** The MCP server isn't authenticated.

**Solution:** Run the authentication command:
```bash
export GOOGLE_OAUTH_CREDENTIALS="$HOME/gcp-oauth.keys.json"
npx @cocal/google-calendar-mcp auth
```

### "Failed to load OAuth credentials"

**Problem:** `gcallm` can't find your OAuth credentials file.

**Solutions:**
1. Verify the file exists:
   ```bash
   ls -la ~/gcp-oauth.keys.json
   ```

2. Configure the path explicitly:
   ```bash
   gcallm setup ~/gcp-oauth.keys.json
   ```

3. Check config:
   ```bash
   cat ~/.config/gcallm/config.json
   ```

### "invalid_grant" error during authentication

**Problem:** OAuth tokens have expired (common in test mode).

**Solution:** Re-authenticate (see [Re-authentication](#re-authentication) below).

### "Access blocked: Authorization Error"

**Problem:** Your email isn't added as a test user, or your app isn't published.

**Solutions:**
1. Go to Google Cloud Console → OAuth consent screen → Test users
2. Add your email address
3. Wait a few minutes for changes to propagate
4. Try authenticating again

### Re-authentication

If your Google Cloud app is in test mode, OAuth tokens expire after 7 days. Re-run the auth command:

```bash
npx @cocal/google-calendar-mcp auth
```

**Tip:** To avoid weekly re-authentication, publish your app in Google Cloud Console (requires verification, but worth it for permanent access).

### "Failed to fetch calendar" errors

**Problem:** Permissions not granted or tokens expired.

**Solutions:**
1. Check that you granted calendar permissions during OAuth flow
2. Re-authenticate:
   ```bash
   npx @cocal/google-calendar-mcp auth
   ```
3. Verify the tokens file exists:
   ```bash
   ls -la ~/.config/google-calendar-mcp/tokens.json
   ```

### Credentials not in default location

If your credentials are in a non-standard location:

1. **Option 1**: Move them to a default location:
   ```bash
   mv /path/to/credentials.json ~/gcp-oauth.keys.json
   ```

2. **Option 2**: Configure the custom path:
   ```bash
   gcallm setup /path/to/credentials.json
   ```

## Configuration Files

`gcallm` stores configuration in these locations:

- **gcallm config**: `~/.config/gcallm/config.json`
  - OAuth credentials path
  - Custom system prompt

- **MCP auth tokens**: `~/.config/google-calendar-mcp/tokens.json`
  - OAuth access/refresh tokens
  - Generated by `npx @cocal/google-calendar-mcp auth`

## Security Notes

- Keep your OAuth credentials file (`gcp-oauth.keys.json`) secure
- Never commit credentials to version control
- Don't share your credentials with others
- The credentials file contains your client ID and secret
- The tokens file (`tokens.json`) contains your personal access tokens

If you suspect your credentials are compromised:
1. Delete the credentials in Google Cloud Console
2. Create new credentials
3. Re-configure `gcallm` with the new credentials
4. Re-authenticate

## Publishing Your App (Optional)

To avoid weekly re-authentication in test mode, you can publish your Google Cloud app:

1. Go to Google Cloud Console → OAuth consent screen
2. Click "**Publish App**"
3. Google may require verification if you're requesting sensitive scopes
4. For personal use apps, you can skip verification by keeping the app in test mode

**Pros of publishing:**
- No token expiration
- No weekly re-authentication needed

**Cons of publishing:**
- May require Google verification
- More complex for personal projects

For most personal use cases, staying in test mode and re-authenticating weekly is simpler.

## See Also

- [CLI Usage Guide](cli.md) - How to use `gcallm` commands
- [Google Calendar MCP Server](https://github.com/nspady/google-calendar-mcp) - The underlying MCP server
- [Google Cloud Console](https://console.cloud.google.com) - Manage your OAuth credentials
