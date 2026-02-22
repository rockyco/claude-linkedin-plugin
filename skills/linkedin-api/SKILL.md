---
name: linkedin-api
description: Use when composing LinkedIn posts, formatting content for LinkedIn, or troubleshooting LinkedIn API issues. Provides knowledge of LinkedIn API conventions, post formatting best practices, and content guidelines.
---

# LinkedIn API Knowledge

## Post Types

LinkedIn supports these post content types via the Posts API (`POST /rest/posts`):

- **Text only**: Just the `commentary` field, no `content` object
- **Single image**: `content.media.id` = image URN
- **Multi-image**: `content.multiImage.images[]` array (2-20 images)
- **Article**: `content.article` with `source` URL, optional `title`, `description`, `thumbnail`
- **Document**: `content.media.id` = document URN (PDF, PPT, etc.)
- **Poll**: Not available via API (LinkedIn web only)

## Required Headers

All LinkedIn REST API calls require:
```
Authorization: Bearer {access_token}
X-Restli-Protocol-Version: 2.0.0
Linkedin-Version: 202601
Content-Type: application/json
```

## Image Upload Flow

1. Initialize: `POST /rest/images?action=initializeUpload` with `owner` URN
2. Upload binary: `PUT {uploadUrl}` with `Content-Type: application/octet-stream`
3. Use the returned `urn:li:image:{id}` in the post's content field

## Post Text Best Practices

- First 3 lines are visible before "see more" - make them count
- Use line breaks for readability (LinkedIn preserves whitespace)
- Hashtags at the end, 3-5 max, relevant to topic
- Tag people with @mentions where appropriate
- **Character limit: ~3000 characters**. The REST API silently truncates longer text with no error. Always validate before posting.
- Aim for 1500-2000 characters for optimal engagement
- Use unicode characters for bullet points if needed

## Character Limit and Truncation

**Critical**: LinkedIn's Posts REST API silently truncates `commentary` text at approximately 3000 characters. There is no error or warning from the API - the post is created with shortened text.

### Recommended workflow for long posts:

1. **Always validate text length** before posting using `validate_text_length()` (built into linkedin-api.py)
2. **Under 3000 chars**: Safe to post via API directly
3. **Over 3000 chars**: Use `--preview` mode:
   - Uploads images to LinkedIn (returns URNs)
   - Validates text length (prints warning)
   - Does NOT create the post
   - Prints LinkedIn compose URL for browser-based posting
4. **Browser-based posting** is the first-class option for long content. LinkedIn's web UI handles text correctly without truncation.

### Preview mode usage:
```bash
# Upload images without posting:
python3 linkedin-api.py post-multi-image --preview --text-file /tmp/post.txt --images img1.png img2.png

# Text-only preview (validates length):
python3 linkedin-api.py post-text --preview --text-file /tmp/post.txt
```

## Author URN

For personal posts: `urn:li:person:{id}`
For company pages: `urn:li:organization:{id}`

The person ID comes from `/v2/userinfo` (the `sub` field) after OAuth with `openid` scope.

## Visibility Options

- `PUBLIC` - visible to anyone on LinkedIn
- `CONNECTIONS` - visible only to connections

## Known API Limitations

- **Silent text truncation**: The Posts API silently truncates `commentary` text at ~3000 characters. No error is returned - the post is created successfully but with shortened text. Always validate text length before creation. Use `--preview` mode for posts near or over the limit.
- **PARTIAL_UPDATE unreliable for commentary**: `X-RestLi-Method: PARTIAL_UPDATE` with `patch: {"$set": {"commentary": "..."}}` returns 204 but may not actually update the text. Do not rely on it to fix truncated posts.
- **Browser editing works**: If text is truncated, edit via LinkedIn's web UI. The internal web APIs correctly handle text updates.
- **Always use --text-file**: Pass post text via a temp file (`--text-file /tmp/linkedin_post.txt`) rather than `--text` on the command line to avoid shell quoting issues with multi-line or special-character text.
- **Preview mode available**: All `post-*` commands support `--preview` to upload media and validate text without creating the post.

## Common Errors

- **401 Unauthorized**: Token expired (60-day lifetime). Re-run `/linkedin:setup`.
- **403 Forbidden**: Missing required scope. Check that "Share on LinkedIn" product is added to the app.
- **422 Unprocessable**: Invalid post payload. Check URN format and required fields.
- **429 Too Many Requests**: Rate limited. Wait and retry.

## Comments API

**Note:** Comments use the `socialActions` endpoint which requires the **Community Management API** product (partner-level access). The basic "Share on LinkedIn" product (`w_member_social`) does NOT cover this endpoint. Apply at https://developer.linkedin.com/product-catalog/marketing/community-management-api.

Comments use the `socialActions` endpoint, separate from the `posts` endpoint.

### List comments
```
GET /rest/socialActions/{postUrn}/comments?start=0&count=20
```
Response `elements[]` array contains: `actor` (URN), `message.text`, `commentUrn`, `id`, `created.time` (ms epoch), `likesSummary.totalLikes`.

### Create a comment
```
POST /rest/socialActions/{postUrn}/comments
Body: {"actor": personUrn, "object": postUrn, "message": {"text": "..."}}
```
Returns comment ID in `x-restli-id` header and full comment object in body.

### Reply to a comment (nested)
```
POST /rest/socialActions/{commentUrn}/comments
Body: {"actor": personUrn, "object": postUrn, "message": {"text": "..."}, "parentComment": commentUrn}
```
The `commentUrn` is composite: `urn:li:comment:(urn:li:activity:xxx,commentId)`.

### Scopes
- Writing comments: `w_member_social` (standard, included with "Share on LinkedIn" product)
- Reading comments: may require `r_member_social` (restricted) for non-own posts

## Scripts Location

The LinkedIn API scripts are at `${CLAUDE_PLUGIN_ROOT}/scripts/`:
- `oauth-server.py` - OAuth 2.0 flow with local callback server
- `linkedin-api.py` - Post creation, image upload, auth check, post verification, preview mode