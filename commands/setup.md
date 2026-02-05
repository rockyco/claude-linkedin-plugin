---
name: setup
description: Set up LinkedIn API authentication (OAuth 2.0)
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
  - WebSearch
---

# LinkedIn OAuth Setup

Guide the user through setting up LinkedIn API authentication. This is a one-time process.

## Step 1: Check existing settings

Read `~/.claude/linkedin.local.md` to see if already authenticated. If the file exists and has a valid (non-expired) token, inform the user they are already set up and ask if they want to re-authenticate.

## Step 2: LinkedIn Developer App

If the user does not have credentials, walk them through creating a LinkedIn Developer App:

1. Tell the user to go to https://www.linkedin.com/developers/apps and click "Create app"
2. They need:
   - App name (anything descriptive)
   - A LinkedIn Company Page to associate with (they can create one if needed)
   - App logo
3. After creating the app, go to the **Auth** tab and:
   - Copy the **Client ID** and **Client Secret**
   - Add `http://localhost:9876/callback` as an **Authorized redirect URL**
4. Go to the **Products** tab and request access to:
   - **Share on LinkedIn** (for w_member_social scope)
   - **Sign In with LinkedIn using OpenID Connect** (for openid and profile scopes)
5. Wait for product access to be approved (usually instant for Share on LinkedIn)

Use AskUserQuestion to collect the Client ID and Client Secret from the user.

## Step 3: Run OAuth flow

Once you have the client_id and client_secret, run the OAuth server:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/oauth-server.py "<client_id>" "<client_secret>"
```

This will:
1. Print an authorization URL and open the user's browser
2. Wait for the OAuth callback on localhost:9876
3. Exchange the authorization code for an access token
4. Fetch the user's profile and person URN
5. Save everything to `~/.claude/linkedin.local.md`

Tell the user to authorize the app in their browser when it opens.

## Step 4: Verify

After the script completes, read `~/.claude/linkedin.local.md` and confirm to the user:
- Their display name
- Their person URN
- Token expiration date (60 days from now)

Tell them they can now use `/linkedin:post` to publish content.

## Important

- Never display the client_secret or access_token in plain text to the user
- The settings file at `~/.claude/linkedin.local.md` contains sensitive credentials
- Token expires after 60 days; re-run `/linkedin:setup` to refresh
