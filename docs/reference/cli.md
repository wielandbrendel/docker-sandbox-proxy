# CLI reference

All commands are available after `pip install -e .` as `sandbox <command>`.

Run `sandbox --help` or `sandbox <command> --help` for the latest flags.

---

## `sandbox init`

Scaffold a new agent configuration directory.

```
sandbox init <name> [--description TEXT]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `name` | Agent name (`[a-z0-9-]` only) |

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--description TEXT` | `""` | Human-readable description written to agent.yaml |

**What it does:**

1. Creates `sandboxes/<name>/` with `agent.yaml`, `.env`, `workspace/`,
   `openclaw-data/`, `gmail-filter-certs/`
2. Allocates a gmail-filter port (incrementing from 8443)
3. Registers the agent in `registry.json`
4. Copies `proxy-bootstrap.cjs` from the mail example template

**Example:**

```bash
sandbox init my-agent --description "Research assistant"
```

**Exit codes:** `0` success, `1` name invalid or directory already exists.

---

## `sandbox start`

Start an agent sandbox.

```
sandbox start <name>
```

**What it does:**

1. Validates Docker Desktop Sandbox support (`docker sandbox --help`)
2. Loads and validates `agent.yaml` (fails fast on unknown keys)
3. Starts `gmail-filter-<name>` container on host (if `gmail_filter.enabled`)
4. Creates the Docker Sandbox VM (idempotent — reuses if exists)
5. Configures the sandbox proxy (allowlist, bypass list, block list)
6. Runs root setup inside the VM (links cron, copies gogcli creds)
7. Generates and writes `sandbox-init.sh`
8. Waits 10 seconds and confirms OpenClaw started

**Example:**

```bash
sandbox start my-agent
```

**Exit codes:** `0` success, `1` preflight failure or Docker error.

---

## `sandbox stop`

Stop an agent sandbox without destroying it.

```
sandbox stop <name>
```

**What it does:**

1. Sends `pkill -f 'openclaw gateway'` inside the VM (graceful shutdown)
2. Waits 3 seconds, then force-kills any remaining OpenClaw processes
3. Stops the Docker Sandbox VM (`docker sandbox stop`)
4. Stops the `gmail-filter-<name>` container (if enabled)

State is preserved — `sandbox start` will resume from where it left off.

**Exit codes:** `0` success (even if sandbox was already stopped).

---

## `sandbox restart`

Stop and start an agent sandbox.

```
sandbox restart <name>
```

Equivalent to `sandbox stop <name> && sandbox start <name>`. Useful after
editing `agent.yaml` or after an unexpected stop.

---

## `sandbox ps`

List all agent sandboxes and their status.

```
sandbox ps
```

Shows a table with columns: Name, Sandbox VM status, Gmail Filter status,
Gmail port. Status is read from `registry.json` and live Docker state.

**Example output:**

```
       Agent Sandboxes
┌──────────┬────────────┬─────────────┬────────────┐
│ Name     │ Sandbox VM │ Gmail Filter│ Gmail Port │
├──────────┼────────────┼─────────────┼────────────┤
│ my-mail  │ running    │ running     │ 8443       │
│ my-agent │ stopped    │ -           │ -          │
└──────────┴────────────┴─────────────┴────────────┘
```

---

## `sandbox logs`

View agent logs.

```
sandbox logs <name> [--service agent|gmail-filter] [-f] [--tail N]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--service TEXT` | `agent` | Which service: `agent` (OpenClaw) or `gmail-filter` |
| `-f`, `--follow` | false | Follow log output (stream) |
| `--tail N` | `100` | Number of lines to show |

For `agent`: tails the most recent OpenClaw log file at
`~/.openclaw/logs/*.log` inside the VM.

For `gmail-filter`: runs `docker logs gmail-filter-<name>`.

**Examples:**

```bash
sandbox logs my-agent
sandbox logs my-agent -f
sandbox logs my-agent --service gmail-filter --tail 50
```

---

## `sandbox shell`

Open an interactive shell inside the sandbox VM.

```
sandbox shell <name> [--root]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--root` | false | Open shell as root instead of the `agent` user |

Opens a bash session as the `agent` user (uid 1000) by default.

**Examples:**

```bash
sandbox shell my-agent
# then: openclaw onboard

sandbox shell my-agent --root
# then: inspect system files, re-run root setup, etc.
```

---

## `sandbox check`

Run preflight checks for an agent without starting it.

```
sandbox check <name>
```

Checks (in order):

1. `.env` file exists in the agent directory
2. Required env vars (all `${VAR}` refs in `agent.yaml`) are non-empty
3. Base image `sandbox-template:latest` is built
4. (If `gmail_filter.enabled` and `TELEGRAM_BOT_TOKEN` set) Telegram `getMe`
   call succeeds

Each check prints `[OK]` or `[FAIL]` with a `fix:` hint for failures.

**Example output:**

```
[OK] .env file: sandboxes/my-agent/.env
[OK] required env vars: all set
[OK] base image sandbox-template:latest: present
[OK] telegram getMe: @MyAgentBot
4 passed, 0 failed
```

**Exit codes:** `0` all checks pass, `1` one or more checks failed.

---

## `sandbox destroy`

Destroy an agent sandbox completely.

```
sandbox destroy <name> [-y] [--purge]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-y`, `--yes` | false | Skip the confirmation prompt |
| `--purge` | false | Also remove the `sandboxes/<name>/` directory |

**What it removes:**

- The Docker Sandbox VM (`docker sandbox rm`)
- The `gmail-filter-<name>` Docker container and its image tag
- The registry entry in `registry.json`

The `sandboxes/<name>/` directory (including `agent.yaml`, workspace, etc.)
is left in place unless `--purge` is used.

**Example:**

```bash
sandbox destroy my-agent --yes
sandbox destroy my-agent --yes --purge  # also removes the directory
```

**Exit codes:** `0` success, `1` aborted or error.

---

## `sandbox config`

Show the fully resolved agent configuration.

```
sandbox config <name>
```

Loads `agent.yaml`, expands all `${VAR}` references, and prints the result as
YAML. Useful for debugging config issues before starting.

**Example:**

```bash
sandbox config my-agent
```

Output:

```yaml
name: my-agent
description: Gmail reader
openclaw:
  version: 2026.5.7
  port: 18789
...
```

---

## `sandbox proxy`

View current proxy rules for a sandbox.

```
sandbox proxy <name>
```

Runs `docker sandbox network proxy <name>` and prints the result. Shows
which domains are currently allowed, bypassed, or blocked.

**Example:**

```bash
sandbox proxy my-agent
```

---

## Global options

| Option | Description |
|--------|-------------|
| `--help` | Show help for the command |
| `--install-completion` | Install shell completion |
| `--show-completion` | Print completion script |
