#!/usr/bin/env python3
"""
LinkedIn OAuth 2.0 local callback server.

Starts a temporary HTTP server on localhost to receive the OAuth callback,
exchanges the authorization code for an access token, fetches the user's
person URN, and writes credentials to the settings file.

Usage:
    python3 oauth-server.py <client_id> <client_secret> [--port PORT]
"""

import http.server
import json
import os
import secrets
import sys
import urllib.parse
import urllib.request
import ssl
import webbrowser
from pathlib import Path

DEFAULT_PORT = 9876
SCOPES = "openid profile w_member_social"
SETTINGS_PATH = Path.home() / ".claude" / "linkedin.local.md"
LINKEDIN_VERSION = "202601"


def get_settings_path():
    return SETTINGS_PATH


def exchange_code_for_token(code, client_id, client_secret, redirect_uri):
    """Exchange authorization code for access token."""
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }).encode()

    req = urllib.request.Request(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read().decode())


def fetch_user_info(access_token):
    """Fetch the authenticated user's profile info and person URN."""
    req = urllib.request.Request(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = json.loads(resp.read().decode())

    person_id = data.get("sub", "")
    name = data.get("name", "Unknown")
    return person_id, name


def save_settings(client_id, client_secret, access_token, person_urn, display_name,
                  expires_in):
    """Write credentials to the settings file."""
    import time
    expires_at = int(time.time()) + expires_in

    content = f"""---
client_id: "{client_id}"
client_secret: "{client_secret}"
access_token: "{access_token}"
person_urn: "{person_urn}"
display_name: "{display_name}"
token_expires_at: {expires_at}
---

# LinkedIn Plugin Settings

Authenticated as **{display_name}** ({person_urn}).

Token expires at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expires_at))}

To re-authenticate, run `/linkedin:setup` again.
"""
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(content)


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """Handle the OAuth redirect callback."""

    def log_message(self, format, *args):
        pass  # Suppress default logging

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" not in params:
            error = params.get("error", ["unknown"])[0]
            error_desc = params.get("error_description", ["No details"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"<h2>Authorization failed</h2><p>{error}: {error_desc}</p>".encode()
            )
            self.server.auth_result = {"error": error, "error_description": error_desc}
            return

        state = params.get("state", [""])[0]
        if state != self.server.expected_state:
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>State mismatch - possible CSRF attack</h2>")
            self.server.auth_result = {"error": "state_mismatch"}
            return

        code = params["code"][0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(
            b"<h2>Authorization successful!</h2>"
            b"<p>You can close this tab and return to Claude Code.</p>"
        )
        self.server.auth_result = {"code": code}


def run_oauth_flow(client_id, client_secret, port=DEFAULT_PORT):
    """Run the full OAuth flow: open browser, catch callback, exchange token."""
    redirect_uri = f"http://localhost:{port}/callback"
    state = secrets.token_urlsafe(32)

    auth_url = (
        "https://www.linkedin.com/oauth/v2/authorization?"
        + urllib.parse.urlencode({
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": SCOPES,
        })
    )

    server = http.server.HTTPServer(("localhost", port), OAuthCallbackHandler)
    server.expected_state = state
    server.auth_result = None

    print(f"OAUTH_URL={auth_url}")
    print(f"REDIRECT_URI={redirect_uri}")
    print("STATUS=waiting_for_callback")
    sys.stdout.flush()

    # Open browser for the user
    webbrowser.open(auth_url)

    # Handle exactly one request (the callback)
    server.handle_request()
    server.server_close()

    result = server.auth_result
    if not result or "error" in result:
        error = result.get("error", "unknown") if result else "no_response"
        desc = result.get("error_description", "") if result else ""
        print(f"ERROR={error} {desc}")
        sys.exit(1)

    code = result["code"]
    print("STATUS=exchanging_token")
    sys.stdout.flush()

    # Exchange code for token
    token_data = exchange_code_for_token(code, client_id, client_secret, redirect_uri)
    access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in", 5184000)

    print("STATUS=fetching_profile")
    sys.stdout.flush()

    # Fetch user info
    person_id, display_name = fetch_user_info(access_token)
    person_urn = f"urn:li:person:{person_id}"

    # Save settings
    save_settings(client_id, client_secret, access_token, person_urn, display_name,
                  expires_in)

    print(f"SUCCESS=Authenticated as {display_name} ({person_urn})")
    print(f"TOKEN_EXPIRES_IN={expires_in}")
    print(f"SETTINGS_PATH={SETTINGS_PATH}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LinkedIn OAuth flow")
    parser.add_argument("client_id", help="LinkedIn app client ID")
    parser.add_argument("client_secret", help="LinkedIn app client secret")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Callback port")
    args = parser.parse_args()

    run_oauth_flow(args.client_id, args.client_secret, args.port)
