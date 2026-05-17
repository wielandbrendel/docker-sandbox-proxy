#!/usr/bin/env bash
# gmail-tool: Access Gmail API through the security filter.
#
# All Gmail API requests go through http://host.docker.internal:8080 via the
# Docker Sandbox proxy. A direct connection to that host:port can be refused
# from inside the sandbox; the proxy rewrites it to the host-side gmail-filter,
# which blocks send/delete operations while allowing read/draft/archive.
#
# Usage:
#   gmail-tool messages list [QUERY]       Search/list messages (default: in:inbox)
#   gmail-tool messages get ID             Read a specific message
#   gmail-tool messages get ID --snippet   Read just the snippet
#   gmail-tool messages archive ID         Archive (remove INBOX label)
#   gmail-tool drafts list                 List drafts
#   gmail-tool drafts create JSON          Create a draft
#   gmail-tool labels list                 List labels
#   gmail-tool profile                     Get user profile
#   gmail-tool raw METHOD PATH [DATA]      Raw API call
#
# Environment:
#   GOG_KEYRING_PASSWORD  (default: sandbox)
#   GOG_ACCOUNT           (required; set in .env)

set -euo pipefail

FILTER="http://host.docker.internal:8080"
ACCOUNT="${GOG_ACCOUNT:?GOG_ACCOUNT not set in environment}"
TOKEN_CACHE="/tmp/.gmail-tool-access-token"
TOKEN_TTL=3000  # seconds (Google tokens last 3600s, refresh at 3000)

# ── Token management (cached, refreshes only when expired) ──

get_access_token() {
    # Return cached token if still valid
    if [ -f "$TOKEN_CACHE" ]; then
        local age=$(( $(date +%s) - $(stat -c %Y "$TOKEN_CACHE" 2>/dev/null || stat -f %m "$TOKEN_CACHE" 2>/dev/null || echo 0) ))
        if [ "$age" -lt "$TOKEN_TTL" ]; then
            cat "$TOKEN_CACHE"
            return
        fi
    fi

    # Export refresh token from gog keyring
    local export_file="/tmp/.gmail-tool-refresh.json"
    if ! GOG_KEYRING_PASSWORD="${GOG_KEYRING_PASSWORD:-sandbox}" \
        gog auth tokens export "$ACCOUNT" --out "$export_file" --overwrite >/dev/null 2>&1; then
        echo "ERROR: gog token export failed. Run: gog auth manage" >&2
        return 1
    fi

    local refresh_token
    refresh_token=$(node -e "try{console.log(JSON.parse(require('fs').readFileSync('$export_file','utf8')).refresh_token)}catch(e){}" 2>/dev/null)
    rm -f "$export_file"

    if [ -z "$refresh_token" ]; then
        echo "ERROR: no refresh token. Run: gog auth manage" >&2
        return 1
    fi

    # Read client credentials
    local creds="$HOME/.config/gogcli/credentials.json"
    if [ ! -f "$creds" ]; then
        echo "ERROR: $creds not found" >&2
        return 1
    fi

    local client_id client_secret
    client_id=$(node -e "console.log(JSON.parse(require('fs').readFileSync('$creds','utf8')).client_id)" 2>/dev/null)
    client_secret=$(node -e "console.log(JSON.parse(require('fs').readFileSync('$creds','utf8')).client_secret)" 2>/dev/null)

    # Exchange refresh token for access token
    local response
    response=$(curl -s --max-time 10 -X POST "https://oauth2.googleapis.com/token" \
        -d "client_id=${client_id}" \
        -d "client_secret=${client_secret}" \
        -d "refresh_token=${refresh_token}" \
        -d "grant_type=refresh_token")

    local token
    token=$(echo "$response" | node -e "
        try {
            const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
            if (d.access_token) { console.log(d.access_token); }
            else { console.error('Token error:', d.error, d.error_description); process.exit(1); }
        } catch(e) { console.error('Parse error:', e.message); process.exit(1); }
    " 2>/dev/null)

    if [ -z "$token" ]; then
        echo "ERROR: token refresh failed" >&2
        return 1
    fi

    # Cache the token
    echo -n "$token" > "$TOKEN_CACHE"
    echo "$token"
}

# ── API call through the gmail-filter ──

api() {
    local method="$1" path="$2"
    shift 2

    local token
    token=$(get_access_token) || exit 1

    local result
    result=$(NO_PROXY="localhost,127.0.0.1" no_proxy="localhost,127.0.0.1" \
        curl -s --max-time 30 "${FILTER}${path}" \
        -X "$method" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        "$@" 2>&1)

    # Check for auth errors (retry once with fresh token)
    if echo "$result" | grep -q '"code": 401' 2>/dev/null; then
        rm -f "$TOKEN_CACHE"
        token=$(get_access_token) || exit 1
        result=$(NO_PROXY="localhost,127.0.0.1" no_proxy="localhost,127.0.0.1" \
            curl -s --max-time 30 "${FILTER}${path}" \
            -X "$method" \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json" \
            "$@" 2>&1)
    fi

    echo "$result"
}

# ── URL-encode helper ──
urlencode() {
    node -e "console.log(encodeURIComponent(process.argv.slice(1).join(' ')))" "$@"
}

# ── Command dispatch ──

CMD="${1:-help}"
SUB="${2:-}"

case "$CMD" in
    messages)
        case "$SUB" in
            list|search|ls)
                shift 2
                QUERY="${*:-in:inbox}"
                api GET "/gmail/v1/users/me/messages?q=$(urlencode "$QUERY")&maxResults=10"
                ;;
            get|read)
                [ -z "${3:-}" ] && { echo "Usage: gmail-tool messages get <ID>" >&2; exit 1; }
                FORMAT="full"
                [ "${4:-}" = "--snippet" ] && FORMAT="metadata"
                api GET "/gmail/v1/users/me/messages/${3}?format=${FORMAT}"
                ;;
            archive)
                [ -z "${3:-}" ] && { echo "Usage: gmail-tool messages archive <ID>" >&2; exit 1; }
                api POST "/gmail/v1/users/me/messages/${3}/modify" \
                    -d '{"removeLabelIds":["INBOX"]}'
                ;;
            modify)
                [ -z "${3:-}" ] || [ -z "${4:-}" ] && { echo "Usage: gmail-tool messages modify <ID> <JSON>" >&2; exit 1; }
                api POST "/gmail/v1/users/me/messages/${3}/modify" -d "$4"
                ;;
            *)
                echo "Usage: gmail-tool messages [list|get|archive|modify] ..." >&2
                exit 1
                ;;
        esac
        ;;
    drafts)
        case "$SUB" in
            list|ls) api GET "/gmail/v1/users/me/drafts" ;;
            create)
                [ -z "${3:-}" ] && { echo "Usage: gmail-tool drafts create <JSON>" >&2; exit 1; }
                api POST "/gmail/v1/users/me/drafts" -d "$3"
                ;;
            delete|rm)
                [ -z "${3:-}" ] && { echo "Usage: gmail-tool drafts delete <ID>" >&2; exit 1; }
                api DELETE "/gmail/v1/users/me/drafts/${3}"
                ;;
            *)
                echo "Usage: gmail-tool drafts [list|create|delete] ..." >&2
                exit 1
                ;;
        esac
        ;;
    labels|label)
        api GET "/gmail/v1/users/me/labels"
        ;;
    profile)
        api GET "/gmail/v1/users/me/profile"
        ;;
    threads)
        case "$SUB" in
            get)
                [ -z "${3:-}" ] && { echo "Usage: gmail-tool threads get <ID>" >&2; exit 1; }
                api GET "/gmail/v1/users/me/threads/${3}?format=full"
                ;;
            *) echo "Usage: gmail-tool threads get <ID>" >&2; exit 1 ;;
        esac
        ;;
    raw)
        # Raw API call: gmail-tool raw GET /gmail/v1/users/me/...
        [ -z "${2:-}" ] || [ -z "${3:-}" ] && { echo "Usage: gmail-tool raw <METHOD> <PATH> [DATA]" >&2; exit 1; }
        if [ -n "${4:-}" ]; then
            api "$2" "$3" -d "$4"
        else
            api "$2" "$3"
        fi
        ;;
    help|--help|-h)
        sed -n '2,/^[^#]/p' "$0" | grep "^#" | sed 's/^# \?//'
        ;;
    *)
        echo "Unknown command: $CMD. Run: gmail-tool help" >&2
        exit 1
        ;;
esac
