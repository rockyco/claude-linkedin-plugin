#!/usr/bin/env python3
"""
LinkedIn API wrapper for posting content.

Supports: text posts, single image, multi-image, articles, and documents.
Uses only Python stdlib (urllib, json, ssl) - no external dependencies.

Usage:
    python3 linkedin-api.py post-text --text "Hello LinkedIn"
    python3 linkedin-api.py post-image --text "Check this out" --images /path/to/img.png
    python3 linkedin-api.py post-multi-image --text "Results" --images img1.png img2.png
    python3 linkedin-api.py post-article --text "Read this" --url https://example.com --title "Title"
    python3 linkedin-api.py upload-image --file /path/to/image.png
    python3 linkedin-api.py get-post --post-id "urn:li:ugcPost:123"
    python3 linkedin-api.py list-comments --post-urn "urn:li:ugcPost:123"
    python3 linkedin-api.py create-comment --post-urn "urn:li:ugcPost:123" --text "Great post!"
    python3 linkedin-api.py reply-comment --post-urn "urn:li:ugcPost:123" --comment-urn "urn:li:comment:(...)" --text "Thanks!"
    python3 linkedin-api.py check-auth
"""

import argparse
import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

SETTINGS_PATH = Path.home() / ".claude" / "linkedin.local.md"
LINKEDIN_VERSION = "202601"
API_BASE = "https://api.linkedin.com/rest"


def load_settings():
    """Load settings from the YAML frontmatter in linkedin.local.md."""
    if not SETTINGS_PATH.exists():
        print("ERROR=Settings file not found. Run /linkedin:setup first.", file=sys.stderr)
        sys.exit(1)

    content = SETTINGS_PATH.read_text()
    if not content.startswith("---"):
        print("ERROR=Invalid settings file format.", file=sys.stderr)
        sys.exit(1)

    # Parse YAML frontmatter (simple key: "value" parsing, no PyYAML needed)
    frontmatter = content.split("---")[1]
    settings = {}
    for line in frontmatter.strip().split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            value = value.strip().strip('"').strip("'")
            settings[key.strip()] = value

    required = ["access_token", "person_urn"]
    for key in required:
        if key not in settings or not settings[key]:
            print(f"ERROR=Missing {key} in settings. Run /linkedin:setup first.",
                  file=sys.stderr)
            sys.exit(1)

    # Check token expiration
    expires_at = int(settings.get("token_expires_at", 0))
    if expires_at and time.time() > expires_at:
        print("ERROR=Access token has expired. Run /linkedin:setup to re-authenticate.",
              file=sys.stderr)
        sys.exit(1)

    return settings


def api_request(method, url, headers, data=None, binary_data=None):
    """Make an API request and return the response."""
    ctx = ssl.create_default_context()

    if binary_data is not None:
        req = urllib.request.Request(url, data=binary_data, headers=headers, method=method)
    elif data is not None:
        req = urllib.request.Request(
            url, data=json.dumps(data).encode(), headers=headers, method=method
        )
    else:
        req = urllib.request.Request(url, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            response_headers = dict(resp.headers)
            body = resp.read().decode()
            return {
                "status": resp.status,
                "headers": response_headers,
                "body": json.loads(body) if body else {},
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"ERROR=API request failed: {e.code} {e.reason}", file=sys.stderr)
        if error_body:
            print(f"DETAILS={error_body}", file=sys.stderr)
        sys.exit(1)


def get_api_headers(access_token, content_type="application/json"):
    """Return standard LinkedIn API headers."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Linkedin-Version": LINKEDIN_VERSION,
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def upload_image(access_token, person_urn, image_path):
    """Upload an image to LinkedIn and return the image URN."""
    image_path = Path(image_path).resolve()
    if not image_path.exists():
        print(f"ERROR=Image file not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    # Step 1: Initialize upload
    init_data = {
        "initializeUploadRequest": {
            "owner": person_urn,
        }
    }

    headers = get_api_headers(access_token)
    resp = api_request(
        "POST",
        f"{API_BASE}/images?action=initializeUpload",
        headers,
        data=init_data,
    )

    body = resp["body"]
    # Handle both wrapped {"value": ...} and direct response formats
    inner = body.get("value", body)
    upload_url = inner["uploadUrl"]
    image_urn = inner["image"]

    # Step 2: Upload binary
    image_bytes = image_path.read_bytes()
    upload_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/octet-stream",
    }

    ctx = ssl.create_default_context()
    req = urllib.request.Request(upload_url, data=image_bytes, headers=upload_headers,
                                method="PUT")
    with urllib.request.urlopen(req, context=ctx) as resp:
        pass  # 201 Created on success

    return image_urn


def create_post(access_token, person_urn, text, content=None, visibility="PUBLIC"):
    """Create a LinkedIn post."""
    post_data = {
        "author": person_urn,
        "commentary": text,
        "visibility": visibility,
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    if content:
        post_data["content"] = content

    headers = get_api_headers(access_token)
    resp = api_request("POST", f"{API_BASE}/posts", headers, data=post_data)

    post_id = resp["headers"].get("x-restli-id", resp["headers"].get("X-Restli-Id", ""))

    # Verify the post text was stored correctly
    if post_id:
        verify_post_text(access_token, post_id, text)

    return post_id


def verify_post_text(access_token, post_id, expected_text):
    """Fetch the created post and verify its commentary matches what was sent."""
    headers = get_api_headers(access_token)
    encoded_urn = urllib.parse.quote(post_id, safe="")
    try:
        resp = api_request("GET", f"{API_BASE}/posts/{encoded_urn}", headers)
        stored = resp["body"].get("commentary", "")
        sent_len = len(expected_text)
        stored_len = len(stored)
        if stored_len < sent_len:
            print(f"WARNING=Text truncated by LinkedIn API: sent {sent_len} chars, "
                  f"stored {stored_len} chars ({stored_len * 100 // sent_len}%)",
                  file=sys.stderr)
            print(f"TRUNCATED_AT={stored[-80:]}", file=sys.stderr)
            print("WARNING=Edit the post via LinkedIn web UI to fix the text. "
                  "The REST API PARTIAL_UPDATE is unreliable for commentary.",
                  file=sys.stderr)
        else:
            print(f"VERIFIED=Post text intact ({stored_len} chars)", file=sys.stderr)
    except SystemExit:
        print("WARNING=Could not verify post text (API read failed)", file=sys.stderr)


def validate_text_length(text, warn_threshold=3000):
    """Check text length and warn if it exceeds LinkedIn's limit.

    Returns True if text is within safe limits, False if over threshold.
    """
    length = len(text)
    if length > warn_threshold:
        print(f"WARNING=Text is {length} chars, exceeds LinkedIn's ~{warn_threshold} char limit. "
              f"Post may be silently truncated by the API.", file=sys.stderr)
        print(f"RECOMMEND=Use --preview to upload images without posting, "
              f"then paste text via LinkedIn's web UI.", file=sys.stderr)
        return False
    print(f"TEXT_LENGTH={length} chars (limit ~{warn_threshold})", file=sys.stderr)
    return True


def resolve_text(args):
    """Get post text from --text or --text-file argument."""
    if hasattr(args, "text_file") and args.text_file:
        p = Path(args.text_file)
        if not p.exists():
            print(f"ERROR=Text file not found: {p}", file=sys.stderr)
            sys.exit(1)
        return p.read_text().strip()
    return args.text


def cmd_check_auth(args):
    """Check authentication status."""
    settings = load_settings()
    expires_at = int(settings.get("token_expires_at", 0))
    remaining = expires_at - int(time.time())
    days_left = remaining // 86400

    print(f"AUTHENTICATED=true")
    print(f"PERSON_URN={settings['person_urn']}")
    print(f"DISPLAY_NAME={settings.get('display_name', 'Unknown')}")
    print(f"TOKEN_DAYS_LEFT={days_left}")


def cmd_post_text(args):
    """Post text-only content."""
    settings = load_settings()
    text = resolve_text(args)
    validate_text_length(text)

    if args.preview:
        print("PREVIEW=Text-only post (no media to upload)")
        print(f"TEXT_LENGTH={len(text)} chars")
        print(f"TEXT_START={text[:120]}...")
        print("COMPOSE_URL=https://www.linkedin.com/feed/?shareActive=true")
        return

    post_id = create_post(
        settings["access_token"],
        settings["person_urn"],
        text,
        visibility=args.visibility,
    )
    print(f"SUCCESS=Post created")
    print(f"POST_ID={post_id}")


def cmd_post_image(args):
    """Post with a single image."""
    settings = load_settings()
    token = settings["access_token"]
    urn = settings["person_urn"]
    text = resolve_text(args)
    validate_text_length(text)

    image_urn = upload_image(token, urn, args.images[0])
    print(f"IMAGE_URN={image_urn}", file=sys.stderr)

    if args.preview:
        print(f"PREVIEW=Single image post")
        print(f"IMAGE_URN={image_urn}")
        print(f"TEXT_LENGTH={len(text)} chars")
        print(f"TEXT_START={text[:120]}...")
        print("COMPOSE_URL=https://www.linkedin.com/feed/?shareActive=true")
        print("NOTE=Image uploaded. Paste text and attach uploaded image via LinkedIn web UI.")
        return

    content = {
        "media": {
            "id": image_urn,
            "title": args.title or "",
        }
    }

    post_id = create_post(token, urn, text, content=content,
                          visibility=args.visibility)
    print(f"SUCCESS=Post with image created")
    print(f"POST_ID={post_id}")


def cmd_post_multi_image(args):
    """Post with multiple images."""
    settings = load_settings()
    token = settings["access_token"]
    urn = settings["person_urn"]
    text = resolve_text(args)
    validate_text_length(text)

    if len(args.images) < 2:
        print("ERROR=Multi-image posts require at least 2 images.", file=sys.stderr)
        sys.exit(1)

    image_urns = []
    for i, img_path in enumerate(args.images):
        print(f"UPLOADING={i+1}/{len(args.images)} {img_path}", file=sys.stderr)
        image_urn = upload_image(token, urn, img_path)
        image_urns.append(image_urn)

    if args.preview:
        print(f"PREVIEW=Multi-image post ({len(image_urns)} images uploaded)")
        for i, urn_val in enumerate(image_urns):
            print(f"IMAGE_{i+1}_URN={urn_val}")
        print(f"TEXT_LENGTH={len(text)} chars")
        print(f"TEXT_START={text[:120]}...")
        print("COMPOSE_URL=https://www.linkedin.com/feed/?shareActive=true")
        print("NOTE=Images uploaded to LinkedIn. To use them: compose a new post in "
              "LinkedIn's web UI, paste your text, and the uploaded images will be "
              "available in your media library.")
        return

    images_payload = []
    alt_texts = args.alt_texts or []
    for i, urn_val in enumerate(image_urns):
        entry = {"id": urn_val}
        if i < len(alt_texts):
            entry["altText"] = alt_texts[i]
        images_payload.append(entry)

    content = {
        "multiImage": {
            "images": images_payload,
        }
    }

    post_id = create_post(token, urn, text, content=content,
                          visibility=args.visibility)
    print(f"SUCCESS=Post with {len(image_urns)} images created")
    print(f"POST_ID={post_id}")


def cmd_post_article(args):
    """Post with an article link."""
    settings = load_settings()
    token = settings["access_token"]
    urn = settings["person_urn"]
    text = resolve_text(args)
    validate_text_length(text)

    if args.preview:
        thumbnail_urn = None
        if args.thumbnail:
            thumbnail_urn = upload_image(token, urn, args.thumbnail)
        print(f"PREVIEW=Article post")
        print(f"ARTICLE_URL={args.url}")
        if args.title:
            print(f"ARTICLE_TITLE={args.title}")
        if thumbnail_urn:
            print(f"THUMBNAIL_URN={thumbnail_urn}")
        print(f"TEXT_LENGTH={len(text)} chars")
        print(f"TEXT_START={text[:120]}...")
        print("COMPOSE_URL=https://www.linkedin.com/feed/?shareActive=true")
        return

    article = {"source": args.url}
    if args.title:
        article["title"] = args.title
    if args.description:
        article["description"] = args.description
    if args.thumbnail:
        thumbnail_urn = upload_image(token, urn, args.thumbnail)
        article["thumbnail"] = thumbnail_urn

    content = {"article": article}

    post_id = create_post(token, urn, text, content=content,
                          visibility=args.visibility)
    print(f"SUCCESS=Article post created")
    print(f"POST_ID={post_id}")


def cmd_get_post(args):
    """Retrieve a post and display its commentary text for verification."""
    settings = load_settings()
    headers = get_api_headers(settings["access_token"])
    encoded_urn = urllib.parse.quote(args.post_id, safe="")
    try:
        resp = api_request("GET", f"{API_BASE}/posts/{encoded_urn}", headers)
    except SystemExit:
        print("VERIFY_FAILED=GET /posts requires additional API permissions (r_member_social).",
              file=sys.stderr)
        print("VERIFY_FAILED=Cannot read post back to verify. Check manually on LinkedIn.",
              file=sys.stderr)
        sys.exit(0)
    body = resp["body"]
    commentary = body.get("commentary", "")
    print(f"COMMENTARY_LENGTH={len(commentary)}")
    print(f"COMMENTARY_START={commentary[:100]}")
    print(f"COMMENTARY_END={commentary[-100:]}")
    print(f"FULL_COMMENTARY={commentary}")


def cmd_list_comments(args):
    """List comments on a post."""
    settings = load_settings()
    headers = get_api_headers(settings["access_token"])

    post_urn = args.post_urn
    encoded_urn = urllib.parse.quote(post_urn, safe="")
    url = f"{API_BASE}/socialActions/{encoded_urn}/comments?start={args.start}&count={args.count}"

    try:
        resp = api_request("GET", url, headers)
    except SystemExit:
        print("LIST_FAILED=Reading comments requires r_member_social scope (restricted).",
              file=sys.stderr)
        print("LIST_FAILED=This scope is only available to select LinkedIn API partners.",
              file=sys.stderr)
        print("LIST_FAILED=View comments on LinkedIn's website instead. "
              "Writing comments (create-comment, reply-comment) still works with w_member_social.",
              file=sys.stderr)
        sys.exit(1)

    comments = resp["body"].get("elements", [])
    if not comments:
        print("NO_COMMENTS=No comments found on this post")
        return

    print(f"COMMENT_COUNT={len(comments)}")
    for i, comment in enumerate(comments):
        actor = comment.get("actor", "unknown")
        text = comment.get("message", {}).get("text", "")
        comment_urn = comment.get("commentUrn", "")
        comment_id = comment.get("id", "")
        created_ms = comment.get("created", {}).get("time", 0)
        created_str = time.strftime("%Y-%m-%d %H:%M:%S",
                                    time.localtime(created_ms / 1000)) if created_ms else "unknown"
        likes = comment.get("likesSummary", {}).get("totalLikes", 0)

        print(f"---COMMENT_{i + 1}/{len(comments)}---")
        print(f"ACTOR={actor}")
        print(f"COMMENT_URN={comment_urn}")
        print(f"COMMENT_ID={comment_id}")
        print(f"CREATED={created_str}")
        print(f"LIKES={likes}")
        print(f"TEXT={text}")


def cmd_create_comment(args):
    """Create a comment on a post."""
    settings = load_settings()
    token = settings["access_token"]
    person_urn = settings["person_urn"]
    headers = get_api_headers(token)

    text = resolve_text(args)
    post_urn = args.post_urn

    data = {
        "actor": person_urn,
        "object": post_urn,
        "message": {"text": text},
    }

    encoded_urn = urllib.parse.quote(post_urn, safe="")
    url = f"{API_BASE}/socialActions/{encoded_urn}/comments"
    resp = api_request("POST", url, headers, data=data)

    comment_id = resp["headers"].get("x-restli-id", resp["headers"].get("X-Restli-Id", ""))
    body = resp.get("body", {})
    comment_urn = body.get("commentUrn", "")
    print(f"SUCCESS=Comment created")
    print(f"COMMENT_ID={comment_id}")
    if comment_urn:
        print(f"COMMENT_URN={comment_urn}")


def cmd_reply_comment(args):
    """Reply to a specific comment."""
    settings = load_settings()
    token = settings["access_token"]
    person_urn = settings["person_urn"]
    headers = get_api_headers(token)

    text = resolve_text(args)
    comment_urn = args.comment_urn
    post_urn = args.post_urn

    data = {
        "actor": person_urn,
        "object": post_urn,
        "message": {"text": text},
        "parentComment": comment_urn,
    }

    encoded_comment_urn = urllib.parse.quote(comment_urn, safe="")
    url = f"{API_BASE}/socialActions/{encoded_comment_urn}/comments"
    resp = api_request("POST", url, headers, data=data)

    reply_id = resp["headers"].get("x-restli-id", resp["headers"].get("X-Restli-Id", ""))
    body = resp.get("body", {})
    reply_urn = body.get("commentUrn", "")
    print(f"SUCCESS=Reply created")
    print(f"REPLY_ID={reply_id}")
    if reply_urn:
        print(f"REPLY_URN={reply_urn}")


def cmd_upload_image(args):
    """Upload an image and return its URN (for use in posts)."""
    settings = load_settings()
    image_urn = upload_image(settings["access_token"], settings["person_urn"], args.file)
    print(f"IMAGE_URN={image_urn}")


def main():
    parser = argparse.ArgumentParser(description="LinkedIn API wrapper")
    sub = parser.add_subparsers(dest="command", required=True)

    # check-auth
    sub.add_parser("check-auth", help="Check authentication status")

    # post-text
    p = sub.add_parser("post-text", help="Create a text-only post")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help="Post text content")
    g.add_argument("--text-file", help="Path to file containing post text")
    p.add_argument("--visibility", default="PUBLIC", choices=["PUBLIC", "CONNECTIONS"])
    p.add_argument("--preview", action="store_true",
                   help="Validate text length without posting. Prints compose URL.")

    # post-image
    p = sub.add_parser("post-image", help="Create a post with one image")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help="Post text content")
    g.add_argument("--text-file", help="Path to file containing post text")
    p.add_argument("--images", nargs=1, required=True, help="Path to image file")
    p.add_argument("--title", default="", help="Image title")
    p.add_argument("--visibility", default="PUBLIC", choices=["PUBLIC", "CONNECTIONS"])
    p.add_argument("--preview", action="store_true",
                   help="Upload image and validate text without posting.")

    # post-multi-image
    p = sub.add_parser("post-multi-image", help="Create a post with multiple images")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help="Post text content")
    g.add_argument("--text-file", help="Path to file containing post text")
    p.add_argument("--images", nargs="+", required=True, help="Paths to image files (2-20)")
    p.add_argument("--alt-texts", nargs="*", help="Alt text for each image")
    p.add_argument("--visibility", default="PUBLIC", choices=["PUBLIC", "CONNECTIONS"])
    p.add_argument("--preview", action="store_true",
                   help="Upload images and validate text without posting.")

    # post-article
    p = sub.add_parser("post-article", help="Create a post with an article link")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help="Post text content")
    g.add_argument("--text-file", help="Path to file containing post text")
    p.add_argument("--url", required=True, help="Article URL")
    p.add_argument("--title", default="", help="Article title")
    p.add_argument("--description", default="", help="Article description")
    p.add_argument("--thumbnail", default="", help="Path to thumbnail image")
    p.add_argument("--visibility", default="PUBLIC", choices=["PUBLIC", "CONNECTIONS"])
    p.add_argument("--preview", action="store_true",
                   help="Upload thumbnail and validate text without posting.")

    # upload-image
    p = sub.add_parser("upload-image", help="Upload an image and get its URN")
    p.add_argument("--file", required=True, help="Path to image file")

    # get-post
    p = sub.add_parser("get-post", help="Retrieve a post to verify its content")
    p.add_argument("--post-id", required=True, help="Post URN (e.g. urn:li:ugcPost:123)")

    # list-comments
    p = sub.add_parser("list-comments", help="List comments on a post")
    p.add_argument("--post-urn", required=True, help="Post URN (e.g. urn:li:ugcPost:123)")
    p.add_argument("--start", type=int, default=0, help="Pagination start index")
    p.add_argument("--count", type=int, default=20, help="Number of comments to return")

    # create-comment
    p = sub.add_parser("create-comment", help="Create a comment on a post")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help="Comment text")
    g.add_argument("--text-file", help="Path to file containing comment text")
    p.add_argument("--post-urn", required=True, help="Post URN to comment on")

    # reply-comment
    p = sub.add_parser("reply-comment", help="Reply to a comment")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help="Reply text")
    g.add_argument("--text-file", help="Path to file containing reply text")
    p.add_argument("--comment-urn", required=True,
                   help="Comment URN to reply to (e.g. urn:li:comment:(urn:li:activity:xxx,yyy))")
    p.add_argument("--post-urn", required=True, help="Original post URN")

    args = parser.parse_args()
    cmd_map = {
        "check-auth": cmd_check_auth,
        "post-text": cmd_post_text,
        "post-image": cmd_post_image,
        "post-multi-image": cmd_post_multi_image,
        "post-article": cmd_post_article,
        "upload-image": cmd_upload_image,
        "get-post": cmd_get_post,
        "list-comments": cmd_list_comments,
        "create-comment": cmd_create_comment,
        "reply-comment": cmd_reply_comment,
    }
    cmd_map[args.command](args)


if __name__ == "__main__":
    main()
