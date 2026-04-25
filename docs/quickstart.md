# Quickstart

From clone to a running sandboxed agent in under 5 minutes (not counting the
one-time Docker image build).

## Prerequisites

- macOS with Docker Desktop 4.40 or later (the `docker sandbox` sub-command is
  required; earlier versions do not have it)
- Python 3.12+
- ~10 GB free disk space for the base image

Linux works too — the Docker Desktop Sandbox behaviour differs slightly (no
idle-sleep), so skip the keepalive step on Linux.

## Step 1: Clone and install

```bash
git clone https://github.com/your-org/docker-sandbox-agents
cd docker-sandbox-agents
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Verify:

```
sandbox --help
```

Expected output:

```
Usage: sandbox [OPTIONS] COMMAND [ARGS]...

 Agent sandbox management CLI

╭─ Commands ────────────────────────────────────────────────────────────────╮
│ init     Scaffold a new agent configuration directory.                    │
│ start    Start an agent sandbox.                                          │
│ stop     Stop an agent sandbox.                                           │
│ restart  Restart an agent sandbox (stop + start).                         │
│ ps       List all agent sandboxes and their status.                       │
│ logs     View agent logs.                                                 │
│ shell    Open interactive shell in sandbox VM.                            │
│ check    Run preflight checks for an agent without starting it.           │
│ destroy  Destroy an agent sandbox completely.                             │
│ config   Show resolved agent configuration.                               │
│ proxy    View current proxy rules for a sandbox.                          │
╰───────────────────────────────────────────────────────────────────────────╯
```

## Step 2: Build the base image

This is a one-time step. The base image is Alpine + Node 22 + pnpm + OpenClaw.
It takes 2-4 minutes on a fast connection.

```bash
docker build -t sandbox-template:latest base-image/sandbox-template/
```

Success looks like:

```
...
Successfully tagged sandbox-template:latest
```

## Step 3: (Optional) Install the keepalive daemon

Docker Desktop on macOS stops the sandbox VM after ~15 minutes of inactivity.
The keepalive daemon wakes it every 2 minutes so your agent stays online.

```bash
bash scripts/install-keepalive.sh
```

Expected output:

```
[keepalive] Copying to /Users/<you>/.local/bin/sandbox-keepalive.sh
[keepalive] Loading plist...
[keepalive] Bootstrapping com.sandbox.keepalive...
[keepalive] Verifying (runs should be > 0)...
[keepalive] OK — runs=1
```

See [troubleshooting.md](troubleshooting.md) if `runs` stays at 0.

## Step 4: Create an agent

```bash
bash scripts/new-agent.sh hello
```

This copies `sandboxes/example-minimal` to `sandboxes/hello` and edits the name.

```
Created sandboxes/hello
  Edit agent.yaml to configure, then run: sandbox start hello
```

## Step 5: Preflight check

```bash
sandbox check hello
```

Expected (before setting up .env):

```
[OK] base image sandbox-template:latest: present
[OK] .env file: sandboxes/hello/.env
[OK] required env vars: all set
3 passed, 0 failed
```

If any line shows `[FAIL]`, follow the `fix:` hint before proceeding.

## Step 6: Start the agent

```bash
sandbox start hello
```

Expected output:

```
Creating Docker Sandbox 'hello'...
  Sandbox created.
Configuring network proxy...
  Policy: deny, 10 allowed, 0 blocked.
Running root setup...
  [root-setup] linked openclaw config
Waiting for OpenClaw to start via entrypoint...
  OpenClaw running (PID 42)
Agent 'hello' started.
```

## Step 7: Onboard OpenClaw

```bash
sandbox shell hello
```

You are now inside the VM. Run:

```
openclaw onboard
```

Follow the prompts. Pick `openai-codex` if you have a Codex subscription, or
any other provider. When done:

```
exit
```

## Step 8: Verify

```bash
sandbox ps
```

Expected:

```
NAME    STATUS    OPENCLAW PORT
hello   running   18789
```

## What next?

- **Add Gmail + Telegram:** follow [docs/mail-quickstart.md](mail-quickstart.md)
- **Customise your agent:** see [docs/customizing.md](customizing.md)
- **Understand the security model:** see [docs/architecture.md](architecture.md)
