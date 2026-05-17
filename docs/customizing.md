# Customizing agents

## Create a new agent

The quickest way is to copy `example-minimal`:

```bash
bash scripts/new-agent.sh my-agent
```

Or copy it manually:

```bash
cp -r sandboxes/example-minimal sandboxes/my-agent
# edit sandboxes/my-agent/agent.yaml — change `name:` to `my-agent`
```

Or scaffold from scratch:

```bash
sandbox init my-agent --description "My custom agent"
```

## Edit agent.yaml

See [docs/reference/agent-yaml.md](reference/agent-yaml.md) for every field.

The most common things to change:

### Adjust the network allowlist

Add domains your agent needs to access:

```yaml
network:
  policy: deny
  allow:
    - "api.openai.com"
    - "*.openai.com"
    - "api.github.com"
    - "*.github.com"
    - "*.npmjs.org"
    - "registry.npmjs.org"
    - "pypi.org"
    - "*.pypi.org"
    - "my-internal-service.example.com"
```

Wildcards (`*.example.com`) match any subdomain. The bare domain
(`example.com`) is separate and must be listed explicitly if needed.

Hosts in `bypass_hosts` (hardcoded in `start.py`) bypass the HTTPS proxy
entirely — they are still allowlisted but not MITM'd. Currently: npm registry,
Telegram API, OpenAI Codex endpoints.

### Pick a port

The OpenClaw gateway uses the port in `openclaw.port`. Default is `18789`.
If you run multiple agents, each needs a different port.

```yaml
openclaw:
  version: "2026.5.7"
  port: 18790
```

Port conflicts are detected by `sandbox init` automatically. If you set it
manually, run `sandbox check my-agent` to verify there is no conflict.

### Mount workspaces

```yaml
workspaces:
  - ~/my-project
  - ~/reference-docs:ro   # read-only
```

Paths are expanded relative to `$HOME`. The workspace is mounted at the same
path inside the VM.

### Add environment variables

```yaml
env:
  TZ: "America/New_York"
  MY_API_KEY: "${MY_API_KEY}"   # expanded from .env at start time
```

Always set `TZ`. Without it, the container defaults to UTC and any
timestamp-aware behaviour (cron, agent responses about time) will be wrong.

### Enable Gmail filter

```yaml
gmail_filter:
  enabled: true
  host_port: 8443     # HTTPS port on host
  http_port: 8080     # HTTP port for agent inside VM
```

See [docs/gmail-filter.md](gmail-filter.md) for what this does.

## Add tools to the base image

If your agent needs system tools (e.g. `ripgrep`, `ffmpeg`, a specific Python
version), add them to the base image Dockerfile:

```dockerfile
# base-image/sandbox-template/Dockerfile
RUN apk add --no-cache ripgrep ffmpeg
```

Then rebuild:

```bash
docker build -t sandbox-template:latest base-image/sandbox-template/
```

All sandboxes share the same base image. Restart any running sandboxes after
rebuilding.

## Add agent-specific scripts

Put scripts in `sandboxes/my-agent/workspace/` — they are mounted inside the
VM and accessible to the agent.

## Configure OpenClaw inside the sandbox

After `sandbox start`, OpenClaw auto-generates `~/.openclaw/openclaw.json`
inside the VM. The file is persisted via the `openclaw-data` volume mount
(`sandboxes/my-agent/openclaw-data/`).

Common things to configure via `openclaw onboard`:
- Authentication provider (openai-codex, anthropic, etc.)
- Telegram bot pairing

Cron jobs are in `sandboxes/my-agent/openclaw-data/cron/jobs.json`. Edit
while the sandbox is stopped, then start it again.

## Multiple agents

Each agent runs independently. They share the base image but have separate
VMs, separate OpenClaw instances, and separate port assignments.

```
sandbox ps          # list all
sandbox start foo   # start one
sandbox stop bar    # stop another
```

## Destroy an agent

This removes the VM, stops any running processes, and removes the runtime
state (`openclaw-data/`, `gmail-filter-certs/`). The `sandboxes/my-agent/`
directory itself is left for you to delete or reuse.

```bash
sandbox destroy my-agent
```
