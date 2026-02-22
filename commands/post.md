---
name: post
description: Compose and publish a post to LinkedIn
argument-hint: "[text or description of what to post]"
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
  - Glob
  - mcp__plugin_playwright_playwright__browser_navigate
  - mcp__plugin_playwright_playwright__browser_snapshot
  - mcp__plugin_playwright_playwright__browser_click
  - mcp__plugin_playwright_playwright__browser_type
  - mcp__plugin_playwright_playwright__browser_fill_form
  - mcp__plugin_playwright_playwright__browser_take_screenshot
---

# LinkedIn Post

Compose and publish content to LinkedIn. Supports text, images, multi-image, and article posts.

## Step 1: Check authentication

Run this to verify credentials:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/linkedin-api.py check-auth
```

If it fails, tell the user to run `/linkedin:setup` first.

## Step 2: Determine post type

Based on the user's request and any arguments provided, determine the post type:

- **Text only**: User provides just text content
- **Single image**: User provides text + one image file path
- **Multi-image**: User provides text + multiple image file paths (2-20 images)
- **Article**: User provides text + a URL to share

If the user's intent is unclear, use AskUserQuestion to clarify:
- What type of post? (text, image, article)
- What images to attach? (ask for file paths)
- Visibility? (PUBLIC or CONNECTIONS only)

## Step 3: Prepare content

Review the post text with the user before publishing:
- Show them the full text that will be posted
- **Check text length**: if over 3000 characters, warn the user that LinkedIn may silently truncate it. Suggest trimming or using preview mode (Step 4a).
- List any images that will be uploaded
- Show the visibility setting
- Ask for confirmation before publishing

If the user provided a draft, show it formatted and ask if they want any changes.

## Step 4: Publish

IMPORTANT: Always write post text to a temp file and use `--text-file`. Never pass long or multi-line text via `--text` on the command line - LinkedIn's API may silently truncate it.

```bash
# 1. Write post text to temp file (use Write tool, not bash heredoc)
#    Write to: /tmp/linkedin_post.txt

# 2. Run the appropriate command with --text-file:
```

### Text only:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/linkedin-api.py post-text --text-file /tmp/linkedin_post.txt
```

### Single image:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/linkedin-api.py post-image --text-file /tmp/linkedin_post.txt --images "/absolute/path/to/image.png"
```

### Multiple images:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/linkedin-api.py post-multi-image --text-file /tmp/linkedin_post.txt --images "/path/to/img1.png" "/path/to/img2.png"
```

### Article:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/linkedin-api.py post-article --text-file /tmp/linkedin_post.txt --url "https://example.com" --title "Article Title"
```

## Step 4a: Preview mode (for long posts or when user prefers browser posting)

Use `--preview` to upload media without creating the post. This is recommended when:
- Text exceeds 3000 characters
- User wants to review/edit in LinkedIn's web UI before publishing
- Previous posts were truncated by the API

```bash
# Upload images without posting:
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/linkedin-api.py post-multi-image --preview --text-file /tmp/linkedin_post.txt --images "/path/to/img1.png" "/path/to/img2.png"
```

After preview:
1. Report the uploaded image URNs to the user
2. Show the compose URL: https://www.linkedin.com/feed/?shareActive=true
3. Tell the user to paste their text and compose in-browser
4. Optionally use Playwright browser tools to help navigate to the compose page

## Step 5: Verify and confirm

After successful posting:
1. Tell the user the post ID (from script output)
2. Try to verify the text was fully stored:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/linkedin-api.py get-post --post-id "POST_ID_HERE"
```
3. If verification fails (403 - needs r_member_social scope), warn the user:
   - "LinkedIn's API may silently truncate post text. Please check the post on LinkedIn to confirm the full text is showing."
   - "If truncated, edit the post directly on LinkedIn's website - the REST API's edit endpoint is unreliable."
4. If verification succeeds but text is truncated:
   - Inform the user of the truncation (sent vs stored char count)
   - Offer to open LinkedIn in the browser via Playwright for editing
   - Provide the direct post URL if available

## Important notes

- Always use absolute paths for image files
- Image files must exist locally (no URLs)
- Multi-image posts need at least 2 and at most 20 images
- **LinkedIn character limit**: The REST API silently truncates `commentary` text around ~3000 characters. No error is returned. Always validate text length before posting.
- The REST API PARTIAL_UPDATE for commentary returns 204 but may not actually update the text. Browser editing is the reliable fallback.
- Always show the user the full post content and ask for confirmation before publishing
- Always use --text-file instead of --text to avoid shell quoting issues and ensure the full text is sent
- When in doubt, use `--preview` mode to upload media safely and let the user finalize in-browser