#!/usr/bin/env bash
# Install the macOS launchd keepalive that prevents Docker Sandbox VMs
# from idling out and restarts the daemon with --vm-idle-timeout 0.
#
# Idempotent: safe to re-run.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC_SH="$REPO_ROOT/sandbox/keepalive/keepalive.sh"
SRC_PLIST="$REPO_ROOT/sandbox/keepalive/com.sandbox.keepalive.plist"

INSTALL_DIR="$HOME/.local/bin"
INSTALL_SH="$INSTALL_DIR/sandbox-keepalive.sh"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$PLIST_DIR/com.sandbox.keepalive.plist"
LABEL="com.sandbox.keepalive"

if [[ "$(uname)" != "Darwin" ]]; then
    echo "This installer is macOS-only (launchd)." >&2
    echo "On Linux, Docker Desktop has no idle-shutdown problem; no keepalive needed." >&2
    exit 1
fi

# IMPORTANT: install location must NOT be under ~/Documents (macOS TCC blocks
# launchd from reading paths there -> exit 126, silent failure).
mkdir -p "$INSTALL_DIR" "$PLIST_DIR"

cp "$SRC_SH" "$INSTALL_SH"
chmod +x "$INSTALL_SH"

# Substitute install path into plist
sed "s|__INSTALL_PATH__|$INSTALL_DIR|g" "$SRC_PLIST" > "$PLIST_PATH"

# Reload
launchctl bootout "gui/$(id -u)" "$PLIST_PATH" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl kickstart "gui/$(id -u)/$LABEL"

# Verify it ran
sleep 3
RUNS=$(launchctl print "gui/$(id -u)/$LABEL" 2>/dev/null | awk '/^\s*runs = /{print $3}')
if [[ "${RUNS:-0}" -lt 1 ]]; then
    echo "ERROR: Keepalive did not run. Check /tmp/sandbox-keepalive.log" >&2
    exit 1
fi

echo "OK Keepalive installed at $INSTALL_SH"
echo "OK Plist at $PLIST_PATH"
echo "OK Verified: ran $RUNS time(s)"
echo "Log: /tmp/sandbox-keepalive.log"
