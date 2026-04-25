#!/usr/bin/env bash
# Create a new agent by cloning sandboxes/example-minimal/ (or example-mail/).
#
# Usage: scripts/new-agent.sh <agent-name> [--mail]

set -euo pipefail

NAME="${1:?usage: $0 <agent-name> [--mail]}"
TEMPLATE="${2:-}"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$REPO_ROOT/sandboxes/example-minimal"
[[ "$TEMPLATE" == "--mail" ]] && SRC="$REPO_ROOT/sandboxes/example-mail"

DST="$REPO_ROOT/sandboxes/$NAME"
if [[ -e "$DST" ]]; then
    echo "Error: $DST already exists" >&2
    exit 1
fi

if [[ ! -d "$SRC" ]]; then
    echo "Error: Template $SRC missing -- has it been created yet?" >&2
    exit 1
fi

cp -R "$SRC" "$DST"

# Update name in agent.yaml
if [[ -f "$DST/agent.yaml" ]]; then
    sed -i.bak "s|^name: .*|name: $NAME|" "$DST/agent.yaml"
    rm "$DST/agent.yaml.bak"
fi

echo "Created sandboxes/$NAME from $(basename "$SRC")"
echo "Next:"
echo "  cd sandboxes/$NAME"
echo "  cp .env.example .env  # then edit"
echo "  sandbox check $NAME"
echo "  sandbox start $NAME"
