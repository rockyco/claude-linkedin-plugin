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
- No strict character limit but aim for under 3000 characters
- Use unicode characters for bullet points if needed

## Author URN

For personal posts: `urn:li:person:{id}`
For company pages: `urn:li:organization:{id}`

The person ID comes from `/v2/userinfo` (the `sub` field) after OAuth with `openid` scope.

## Visibility Options

- `PUBLIC` - visible to anyone on LinkedIn
- `CONNECTIONS` - visible only to connections

## Known API Limitations

- **Silent text truncation**: The Posts API may silently truncate `commentary` text server-side. There is no error returned - the post is created successfully but with shortened text. Always verify after creation by reading the post back via `GET /rest/posts/{encoded_urn}`.
- **PARTIAL_UPDATE unreliable for commentary**: `X-RestLi-Method: PARTIAL_UPDATE` with `patch: {"$set": {"commentary": "..."}}` returns 204 but may not actually update the text. Do not rely on it to fix truncated posts.
- **Browser editing works**: If text is truncated, edit via LinkedIn's web UI. The internal web APIs correctly handle text updates.
- **Always use --text-file**: Pass post text via a temp file (`--text-file /tmp/linkedin_post.txt`) rather than `--text` on the command line to avoid shell quoting issues with multi-line or special-character text.

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
- `linkedin-api.py` - Post creation, image upload, auth check, post verification
