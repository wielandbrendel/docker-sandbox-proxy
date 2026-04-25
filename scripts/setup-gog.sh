#!/usr/bin/env bash
# Walk the user through setting up gogcli OAuth credentials for Gmail access.

set -euo pipefail

cat <<'EOF'
gogcli OAuth setup
==================

You need a Google Cloud project with a Desktop OAuth client.

Step 1: Go to https://console.cloud.google.com/apis/credentials
Step 2: Create a new project (or pick an existing one)
Step 3: Click "Create Credentials" -> "OAuth client ID" -> "Desktop app"
Step 4: Download the JSON file. Open it and confirm it has top-level "installed".
        If it has "web" instead, you picked the wrong app type -- start over.
Step 5: Save it to ~/.config/gogcli/credentials.json

Press ENTER when done...
EOF

read -r

CREDS="$HOME/.config/gogcli/credentials.json"
if [[ ! -f "$CREDS" ]]; then
    echo "Error: $CREDS not found" >&2
    exit 1
fi

if ! grep -q '"installed"' "$CREDS"; then
    echo "Error: $CREDS does not have top-level \"installed\" -- wrong OAuth app type" >&2
    echo "  Re-create as Desktop app." >&2
    exit 1
fi

echo "OK: credentials.json looks valid"
echo "Next: run 'gog auth manage' to complete OAuth flow for your Google account"
