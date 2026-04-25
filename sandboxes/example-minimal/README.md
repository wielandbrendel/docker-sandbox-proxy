# example-minimal

The simplest possible sandboxed OpenClaw agent. No Gmail, no Telegram, no
extra integrations — just an isolated OpenClaw with proxy-bound network.

## Quickstart

From the repo root:

```
bash scripts/new-agent.sh hello
cd sandboxes/hello
cp .env.example .env  # edit if you have env vars
sandbox check hello
sandbox start hello
sandbox shell hello
# inside the sandbox:
openclaw onboard
```

## What's in this directory

- `agent.yaml` — main config (name, network policy, OpenClaw version, resources)
- `.env.example` — template for secrets
- `workspace/` — the agent's working directory (mounted into the sandbox)

`.env`, `openclaw-data/`, and other runtime state are gitignored.
