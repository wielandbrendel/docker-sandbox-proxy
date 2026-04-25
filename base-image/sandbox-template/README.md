# sandbox-template base image

Alpine + Node 22 + pnpm + OpenClaw 2026.4.11 + gogcli, pre-installed.

## Build

```
docker build -t sandbox-template:latest base-image/sandbox-template/
```

## What it provides

- Pre-installed OpenClaw — agents start in <2s instead of pnpm-installing on first boot
- `agent` user (uid 1000) with sudo for setup tasks
- `docker` group (required by the Docker Sandbox daemon for socket access)
- Auto-running entrypoint that finds and runs `<workspace>/sandbox-init.sh`

## Customizing

Modify `Dockerfile` to add tools your agents need. After changes, rebuild
and re-create your sandbox (`sandbox destroy <name> && sandbox start <name>`).
