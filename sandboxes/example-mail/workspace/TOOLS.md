# Tools

## Network ports

This container reserves port 18789 for the OpenClaw gateway.
Pick any free local port for dashboards or dev servers.

## Gmail

Use `bash gmail-tool.sh ...` (see `gmail-tool.sh help`). Direct access to
`gmail.googleapis.com` is blocked — only the filtered tool works.

## Telegram

Inside the agent loop, Telegram messages arrive automatically. To send,
use OpenClaw's announce/reply mechanism.
