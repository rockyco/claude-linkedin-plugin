---
name: comments
description: View and reply to comments on a LinkedIn post
argument-hint: "[post URN or 'latest']"
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
  - Glob
---

# LinkedIn Comments

View comments on a LinkedIn post and reply to them.

## Prerequisites

The comments API uses LinkedIn's `socialActions` endpoint which requires the **Community Management API** product (partner-level access). The basic "Share on LinkedIn" product (`w_member_social`) does NOT grant access to these endpoints.

If the user hasn't applied for Community Management API access, the API commands will fail with 403. In that case, inform the user and suggest they interact with comments via LinkedIn's website.

## Step 1: Check authentication

Run this to verify credentials:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/linkedin-api.py check-auth
```

If it fails, tell the user to run `/linkedin:setup` first.

## Step 2: Determine the post URN

The user needs to provide a post URN (e.g. `urn:li:ugcPost:123` or `urn:li:share:456`).

If the user says "latest" or doesn't specify, check if there's a recent post URN from the current session. If not, ask the user for the post URN - they can find it from a previous `/linkedin:post` output or from the LinkedIn URL of the post.

## Step 3: Try to list comments

Try listing comments via the API:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/linkedin-api.py list-comments --post-urn "POST_URN_HERE"
```

**If listing succeeds**: Display comments in a readable format with numbering, text, timestamp, and comment URN for each.

**If listing fails (403 - expected for most users)**: The `r_member_social` scope required for reading comments is restricted to select API partners. Tell the user:
- They can view comments on LinkedIn's website
- The user can provide the comment URN from LinkedIn's web interface if they want to reply
- Creating new top-level comments still works without this scope

## Step 4: Handle user actions

Use AskUserQuestion to ask the user what they want to do:
- Reply to a specific comment (user must provide comment URN if listing failed)
- Add a new top-level comment
- Done / exit

### Reply to a comment

1. If comment listing worked, ask which comment number to reply to
2. If comment listing failed, ask the user for the comment URN (they can find it in the LinkedIn web UI page source or network inspector)
3. Ask for the reply text, or let the user provide it
3. Show the reply text and ask for confirmation
4. Write the reply text to a temp file and execute:

```bash
# Write reply text to /tmp/linkedin_reply.txt using the Write tool

python3 ${CLAUDE_PLUGIN_ROOT}/scripts/linkedin-api.py reply-comment \
  --post-urn "POST_URN_HERE" \
  --comment-urn "COMMENT_URN_HERE" \
  --text-file /tmp/linkedin_reply.txt
```

### Add a top-level comment

1. Ask for the comment text
2. Show the comment text and ask for confirmation
3. Write the comment text to a temp file and execute:

```bash
# Write comment text to /tmp/linkedin_comment.txt using the Write tool

python3 ${CLAUDE_PLUGIN_ROOT}/scripts/linkedin-api.py create-comment \
  --post-urn "POST_URN_HERE" \
  --text-file /tmp/linkedin_comment.txt
```

## Step 5: Confirm result

After posting a comment or reply:
1. Show the comment/reply ID from the script output
2. Offer to list comments again to verify it was posted

## Important notes

- Comment URNs are composite: `urn:li:comment:(urn:li:activity:xxx,yyy)` - always use the full URN including parentheses
- The `w_member_social` scope (from Share on LinkedIn product) allows writing comments
- Reading comments may require `r_member_social` (restricted scope) - if listing fails, advise the user to check comments via LinkedIn's web UI instead
- Always use `--text-file` for comment/reply text to avoid shell quoting issues
- Always show the user the text and ask for confirmation before posting
