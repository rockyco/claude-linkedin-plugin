# Claude Code LinkedIn Plugin

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) plugin for publishing content to LinkedIn directly from your terminal. Supports text posts, single/multi-image posts, article shares, and comment interactions.

Zero external dependencies - uses only Python stdlib (`urllib`, `json`, `ssl`).

## Features

- `/linkedin:setup` - OAuth 2.0 authentication flow with local callback server
- `/linkedin:post` - Compose and publish posts (text, images, articles)
- `/linkedin:status` - Check authentication status and token health
- `/linkedin:comments` - View and reply to post comments (requires Community Management API)

## Installation

Clone this repo into your Claude Code plugins directory:

```bash
git clone https://github.com/rockyco/claude-linkedin-plugin.git ~/.claude/plugins/linkedin
```

Then restart Claude Code. The plugin will be auto-discovered.

## Setup

Run `/linkedin:setup` in Claude Code. It will walk you through:

1. Creating a LinkedIn Developer App at https://www.linkedin.com/developers/apps
2. Enabling the **Share on LinkedIn** and **Sign In with LinkedIn using OpenID Connect** products
3. Adding `http://localhost:9876/callback` as an authorized redirect URL
4. Running the OAuth flow to obtain and store your access token

Credentials are stored locally in `~/.claude/linkedin.local.md` (excluded from version control).

## Usage

### Post text

```
/linkedin:post Here is my latest update about the project
```

### Post with images

```
/linkedin:post Check out these results --images /path/to/chart1.png /path/to/chart2.png
```

### Share an article

```
/linkedin:post Read my new blog post --url https://example.com/post
```

### Check status

```
/linkedin:status
```

### View/reply to comments

```
/linkedin:comments urn:li:share:1234567890
```

> **Note:** The comments feature requires LinkedIn's **Community Management API** product, which is separate from the basic "Share on LinkedIn" product. See the [Comments API](#comments-api) section below.

## Post Types

| Type | Description |
|------|-------------|
| Text only | Just the `commentary` field |
| Single image | One image attachment |
| Multi-image | 2-20 image attachments |
| Article | URL share with optional title, description, thumbnail |

## Known API Limitations

- **Silent text truncation**: LinkedIn's Posts API may silently truncate `commentary` text server-side. No error is returned - the post is created successfully but with shortened text. This has been observed on multi-image and article posts. The plugin automatically verifies post text after creation when possible.
- **PARTIAL_UPDATE unreliable**: The REST API's `PARTIAL_UPDATE` for commentary returns 204 but does not actually update the text. Do not rely on it to fix truncated posts.
- **Browser-edit workaround**: If truncation occurs, the plugin can fix it by opening the post in LinkedIn's web UI via Playwright, clicking "Edit post", appending the missing text with `keyboard.insertText()`, and saving. LinkedIn's internal web API correctly handles the full text update.
- **Always use --text-file**: The plugin writes post text to a temp file internally to avoid shell quoting issues and ensure the full text is sent to the API.

## Comments API

The comments feature uses LinkedIn's `socialActions` endpoint, which requires the **Community Management API** product - a separate partner-level access tier. The basic "Share on LinkedIn" product (`w_member_social` scope) does **not** grant access to these endpoints.

Key constraints:
- Community Management API requires its own dedicated LinkedIn app (cannot coexist with "Share on LinkedIn" on the same app)
- Application requires a business email for verification (personal email domains like Gmail are rejected)
- Apply at https://developer.linkedin.com/product-catalog/marketing/community-management-api

The comment commands (`list-comments`, `create-comment`, `reply-comment`) are implemented and ready to use once you have the required API access.

## Project Structure

```
.claude-plugin/
  plugin.json          # Plugin manifest
commands/
  setup.md             # OAuth setup workflow
  post.md              # Post creation workflow
  status.md            # Auth status check
  comments.md          # Comment viewing/replying workflow
scripts/
  oauth-server.py      # OAuth 2.0 local callback server
  linkedin-api.py      # API wrapper (posts, images, comments)
skills/
  linkedin-api/
    SKILL.md           # LinkedIn API knowledge base
```

## API Version

This plugin uses LinkedIn REST API version `202601`. LinkedIn sunsets API versions approximately one year after release. If you encounter version-related errors, check the [LinkedIn API versioning docs](https://learn.microsoft.com/en-us/linkedin/marketing/versioning) for the current active version and update the `LINKEDIN_VERSION` constant in both Python scripts.

## Requirements

- Python 3.8+
- Claude Code CLI
- A LinkedIn account with a Developer App

## License

MIT
