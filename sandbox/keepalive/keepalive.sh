#!/usr/bin/env bash
# Sandbox keepalive: ensures sandbox VMs stay alive and the daemon
# runs with --vm-idle-timeout 0 (no idle shutdown).
#
# Runs every 2 minutes via macOS launchd.
# IMPORTANT: This script MUST be installed OUTSIDE ~/Documents (e.g.
# ~/.local/bin/sandbox-keepalive.sh). macOS TCC denies launchd access
# to ~/Documents — a plist pointing into ~/Documents fails silently
# with exit code 126 ("Operation not permitted") and the VM eventually
# stops despite --vm-idle-timeout 0.
#
# Install:
#   mkdir -p ~/.local/bin
#   cp sandbox/keepalive/keepalive.sh ~/.local/bin/sandbox-keepalive.sh
#   chmod +x ~/.local/bin/sandbox-keepalive.sh
#   # Plist must point at ~/.local/bin/sandbox-keepalive.sh (NOT this file)
#   cp sandbox/keepalive/com.sandbox.keepalive.plist ~/Library/LaunchAgents/
#   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.sandbox.keepalive.plist

set -euo pipefail

# launchd has a minimal PATH; make sure docker is findable.
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

# ── Ensure daemon runs with --vm-idle-timeout 0 ──
# Docker Desktop starts the daemon with default 30m timeout on app restart.
DAEMON_PID=$(pgrep -f "docker-sandbox daemon start" 2>/dev/null | head -1)
if [ -n "$DAEMON_PID" ]; then
    DAEMON_CMD=$(ps -p "$DAEMON_PID" -o args= 2>/dev/null)
    if ! echo "$DAEMON_CMD" | grep -q "vm-idle-timeout"; then
        docker sandbox daemon stop 2>/dev/null || true
        sleep 1
        docker sandbox daemon start --detach --vm-idle-timeout 0 2>/dev/null
    fi
fi

# ── Ping each running sandbox to keep its VM alive ──
# Use `docker sandbox ls` (which does not read files in ~/Documents).
SANDBOXES=$(docker sandbox ls 2>/dev/null | awk 'NR>1 {print $1}' || true)
for name in $SANDBOXES; do
    [ -z "$name" ] && continue
    docker sandbox exec -u agent "$name" true 2>/dev/null || true
done

echo "[$(date -u +%FT%TZ)] keepalive ran for: ${SANDBOXES:-<none>}"
