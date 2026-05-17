# agent.yaml reference

Every agent is configured by a single `agent.yaml` file in its
`sandboxes/<name>/` directory. All fields are validated on `sandbox start`
with unknown keys causing an immediate error (no crash-loop later).

Source of truth: `sandbox/config/schema.py`.

---

## Top-level fields

### `name`

**Type:** string (required)
**Pattern:** `[a-z0-9-]+` (lowercase, digits, hyphens only)

Identifies the agent. Must match the directory name in `sandboxes/`. Used as
the Docker Sandbox name and as a prefix for the `gmail-filter` container.

```yaml
name: my-agent
```

---

### `description`

**Type:** string
**Default:** `""`

Human-readable description. Not used programmatically.

```yaml
description: "Gmail reader with Telegram interface"
```

---

### `workspaces`

**Type:** list of strings
**Default:** `[]` (falls back to the agent directory itself)

Host paths to mount into the sandbox VM. Each entry is a path, optionally
suffixed with `:ro` for read-only.

Paths are expanded with `Path.expanduser()` so `~/` works.

```yaml
workspaces:
  - ~/my-project
  - ~/reference-docs:ro
```

If empty, `sandbox start` mounts the `sandboxes/<name>/` directory.

---

### `env`

**Type:** dict (string → string)
**Default:** `{}`

Environment variables injected into the agent at start time. Values of the
form `${VAR}` are expanded from the host environment or from `.env`.

**Always set `TZ`**. Without it the container defaults to UTC and timestamps
in logs, cron schedules, and agent responses will be wrong for users in other
timezones.

```yaml
env:
  TZ: "Europe/Berlin"
  MY_API_KEY: "${MY_API_KEY}"
```

---

### `env_file`

**Type:** string
**Default:** `""`

Path (relative to `sandboxes/<name>/`) of an `.env` file. Variables from this
file are expanded into `${VAR}` references in `agent.yaml`.

```yaml
env_file: .env
```

Typical contents of `.env`:

```bash
TELEGRAM_BOT_TOKEN=1234567890:AAE...
TELEGRAM_CHAT_ID=123456789
GOG_ACCOUNT=you@example.com
```

---

### `restart_policy`

**Type:** string
**Default:** `"unless-stopped"`

Passed to the keepalive logic. Not directly a Docker restart policy (the
sandbox VM does not use Docker Compose), but the entrypoint script respects it
for the OpenClaw gateway restart loop.

Valid values: `"unless-stopped"`, `"always"`, `"no"`.

---

## `openclaw` section

Controls the OpenClaw gateway process inside the VM.

```yaml
openclaw:
  version: "2026.5.7"
  port: 18789
```

### `openclaw.version`

**Type:** string
**Default:** `"2026.5.7"`

OpenClaw version to run. The base image ships a pinned version; changing this
requires rebuilding the base image unless the new version is already installed.

### `openclaw.port`

**Type:** integer
**Default:** `18789`

Port the OpenClaw gateway listens on inside the VM. Must be unique across all
running agents if you expose them to the host.

---

## `gmail_filter` section

Controls the optional Gmail operation filter.

```yaml
gmail_filter:
  enabled: false
  host_port: 8443
  http_port: 8080
```

### `gmail_filter.enabled`

**Type:** bool
**Default:** `false`

When `true`, `sandbox start` starts a `gmail-filter-<name>` container on the
host and redirects Gmail API traffic through it. The filter blocks send,
delete, and settings-change operations; reads and draft creation are allowed.

See [docs/gmail-filter.md](../gmail-filter.md) for the full allowlist.

### `gmail_filter.host_port`

**Type:** integer
**Default:** `8443`

HTTPS port the gmail-filter container binds to on the host. Must be unique
across agents. `sandbox init` assigns this automatically to avoid conflicts.

### `gmail_filter.http_port`

**Type:** integer
**Default:** `8080`

HTTP port the gmail-filter container binds to on the host, used by the sandbox
agent to reach the filter via `localhost`. Must also be unique across agents.

---

## `network` section

Controls which domains the agent can reach.

```yaml
network:
  policy: deny
  allow:
    - "api.openai.com"
    - "*.openai.com"
```

### `network.policy`

**Type:** string
**Default:** `"deny"`

Network policy for outbound traffic. Valid values:

- `"deny"` — deny-by-default; only domains in `allow` are reachable
- `"allow"` — allow-by-default; `allow` list is ignored

Almost always use `"deny"`. The `allow` policy is intended for debugging only.

### `network.allow`

**Type:** list of strings
**Default:** `[]`

Domains the agent is permitted to access. Wildcards (`*.example.com`) match
any subdomain. The bare domain (`example.com`) is separate.

These entries are passed to `docker sandbox proxy` as `allow_hosts`.

In addition to this list, some hosts are hardcoded as `bypass_hosts` in
`start.py` (npm registry, Telegram API, OpenAI Codex) because they are
incompatible with HTTPS MITM. They are still blocked unless they would be
reachable under the policy.

---

## `resources` section

CPU and memory limits for the sandbox VM.

```yaml
resources:
  cpus: "4"
  memory: "8g"
```

### `resources.cpus`

**Type:** string
**Default:** `"4"`

Number of CPU cores available to the VM. Passed to `docker sandbox create`.

### `resources.memory`

**Type:** string
**Default:** `"8g"`

Memory limit for the VM. Accepts Docker-style suffixes: `"4g"`, `"512m"`.

---

## Full example

```yaml
name: my-mail
description: "Gmail reader and Telegram assistant"

openclaw:
  version: "2026.5.7"
  port: 18789

workspaces:
  - ~/my-project
  - ~/reference:ro

env:
  TZ: "Europe/Berlin"
  TELEGRAM_BOT_TOKEN: "${TELEGRAM_BOT_TOKEN}"
  TELEGRAM_CHAT_ID: "${TELEGRAM_CHAT_ID}"
  GOG_ACCOUNT: "${GOG_ACCOUNT}"

env_file: .env

gmail_filter:
  enabled: true
  host_port: 8443
  http_port: 8080

network:
  policy: deny
  allow:
    - "api.telegram.org"
    - "*.api.telegram.org"
    - "*.openai.com"
    - "chatgpt.com"
    - "*.chatgpt.com"
    - "*.github.com"
    - "*.npmjs.org"
    - "*.pypi.org"
    - "oauth2.googleapis.com"
    - "*.accounts.google.com"

resources:
  cpus: "4"
  memory: "8g"

restart_policy: unless-stopped
```
