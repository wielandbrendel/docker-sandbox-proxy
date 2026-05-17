# Tools

## Network ports

This container reserves port 18789 for the OpenClaw gateway.
Pick any free local port for dashboards or dev servers.

## Gmail

Use `gmail-tool ...` when available on `PATH`, or `bash gmail-tool.sh ...` from
the sandbox directory (see `gmail-tool help`). Direct access to
`gmail.googleapis.com` is blocked; only the filtered tool works.

Do not use raw `curl http://host.docker.internal:8080/...` as a health check.
Direct sockets to that endpoint may be refused from inside the sandbox; the
wrapper intentionally reaches it through the Docker Sandbox proxy.

## Telegram

Inside the agent loop, Telegram messages arrive automatically. To send,
use OpenClaw's announce/reply mechanism.
