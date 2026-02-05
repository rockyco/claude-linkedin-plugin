---
name: status
description: Check LinkedIn authentication status and token health
allowed-tools:
  - Bash
  - Read
---

# LinkedIn Status

Check the current LinkedIn authentication status.

## Action

Run the auth check:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/linkedin-api.py check-auth
```

Also read `~/.claude/linkedin.local.md` for the full settings.

## Report to user

Tell the user:
- Whether they are authenticated
- Their display name and person URN
- How many days until the token expires
- If the token is expired, tell them to run `/linkedin:setup` to re-authenticate

Do NOT display the access_token or client_secret values.
