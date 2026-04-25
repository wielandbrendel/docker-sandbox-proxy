# Troubleshooting

## 1. Agent stopped responding

### Symptom
The Telegram bot does not reply. `sandbox ps` shows `stopped` or the agent was
working yesterday but is silent today.

### Root cause A: VM idle timeout

Docker Desktop on macOS stops sandbox VMs after ~15 minutes of inactivity.

**Fix:** Install the keepalive daemon:

```bash
bash scripts/install-keepalive.sh
```

Verify it is running:

```bash
launchctl print gui/$(id -u)/com.sandbox.keepalive | grep runs
```

`runs` should be greater than 0. If it is 0, see the keepalive section below.

**Immediate fix:** restart the sandbox:

```bash
sandbox start my-agent
```

### Root cause B: OpenClaw gateway crash-loop

The gateway process restarts on crash. If it keeps crashing, check logs:

```bash
sandbox logs my-agent
```

Look for `Error:` lines or `SchemaValidationError`. Common cause: unknown key
in `~/.openclaw/openclaw.json` inside the sandbox (the gateway rejects the
config with `extra=forbid`).

**Fix:**

```bash
sandbox shell my-agent
# edit ~/.openclaw/openclaw.json — remove unrecognised keys
exit
sandbox restart my-agent
```

### Root cause C: OAuth token expired

If logs show `token refresh failed for openai-codex`:

**Fix:** re-onboard:

```bash
sandbox shell my-agent
openclaw onboard --auth-choice openai-codex
exit
```

---

## 2. Cron jobs don't fire

### Symptom
Scheduled jobs (daily summaries, etc.) are not running.

### Root cause A: Cron symlink missing

OpenClaw looks for cron jobs at `~/.openclaw/cron/jobs.json` inside the
sandbox. If the sandbox was recreated, the symlink from the mounted volume
may be broken.

**Fix:** `sandbox start` runs `init_script.py` which re-creates the symlink.
Restart the sandbox:

```bash
sandbox restart my-agent
```

### Root cause B: `consecutiveErrors` field is set

If a cron job fails repeatedly, OpenClaw sets `consecutiveErrors` in the job
and stops running it.

**Fix:** edit `sandboxes/my-agent/openclaw-data/cron/jobs.json`, find the
job, and reset `"consecutiveErrors": 0`. Do this while the sandbox is stopped
or the file may be overwritten:

```bash
sandbox stop my-agent
# edit the file
sandbox start my-agent
```

### Root cause C: Wrong session/payload combination

See the architecture notes on cron delivery constraints. The reliable pattern is:
- `sessionTarget: "isolated"`, `payload.kind: "agentTurn"`, `delivery.mode: "none"`
- Have the agent explicitly announce the result to the main session.

Using `sessionTarget: "main"` with `agentTurn` is rejected. Using `announce`
delivery from an isolated session fails silently.

---

## 3. Keepalive not running

### Symptom
`launchctl print gui/$(id -u)/com.sandbox.keepalive` shows `runs = 0` or the
service does not exist.

### Root cause A: TCC blocks the script location

macOS TCC blocks launchd services in `~/Documents/`. The script must live in
`~/.local/bin/`.

**Fix:** The installer puts it in the right place. If you installed manually
from a different path, reinstall:

```bash
bash scripts/install-keepalive.sh
```

### Root cause B: Plist not loaded

```bash
launchctl bootout gui/$(id -u)/com.sandbox.keepalive 2>/dev/null
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.sandbox.keepalive.plist
launchctl kickstart -k gui/$(id -u)/com.sandbox.keepalive
```

### Root cause C: `StartInterval` throttling

If you edited the plist to use `StartInterval`, macOS throttles it when
the system is idle. Use `StartCalendarInterval` instead. The installer uses
the correct form automatically.

---

## 4. OAuth token refresh failed

### Symptom
Logs contain: `OAuth token refresh failed for openai-codex` or similar.

### Fix

Re-onboard the affected provider:

```bash
sandbox shell my-agent
openclaw onboard --auth-choice openai-codex
exit
```

For `gogcli` (Gmail OAuth), re-authenticate on the host:

```bash
gog auth manage
```

Then restart:

```bash
sandbox restart my-agent
```

---

## 5. Schema validation crash-loop

### Symptom
`sandbox start` or `sandbox logs` shows a schema validation error like:
`extra fields not permitted` or `unexpected key 'agents.defaults.foo'`.

### Root cause

`agent.yaml` or `openclaw.json` contains a key that the current version
does not recognise. The CLI validates `agent.yaml` with `extra=forbid` before
starting, so this will produce a clear error at `sandbox start` time. The
gateway validates `openclaw.json` on startup.

**Fix:** read the error message — it names the bad key. Remove it from the
config file:

```bash
sandbox config my-agent   # shows resolved config; errors show here
```

For `openclaw.json` issues:

```bash
sandbox shell my-agent
cat ~/.openclaw/openclaw.json
# remove unrecognised keys
exit
sandbox restart my-agent
```

---

## 6. Telegram bot does not respond

### Symptom
Messages to the bot are ignored. No pairing code was received, or pairing was
done but the bot never replies.

### Root cause A: Pairing not approved

After the first DM, approve the pairing:

```bash
sandbox shell my-agent
openclaw pairing approve telegram <CODE>
exit
```

### Root cause B: DM allowlist

OpenClaw has a per-user allow list. If the Telegram user ID is not in the
allow list (`gateway.allowedSenders` or similar in `openclaw.json`), messages
are silently dropped.

**Fix:** check `~/.openclaw/openclaw.json` inside the sandbox for allowlist
settings. Add your user ID.

### Root cause C: Wrong bot token

Run `sandbox check my-agent` — it calls `getMe` and reports whether the token
is valid:

```
[OK] telegram getMe: @YourBotName
```

If it shows `[FAIL]`, regenerate the token via BotFather: `/mybots` → select
your bot → API token → Revoke current token → copy new token → update `.env`
→ `sandbox restart my-agent`.

### Root cause D: `TELEGRAM_CHAT_ID` is a username instead of numeric ID

The `TELEGRAM_CHAT_ID` must be the numeric user ID (e.g. `123456789`), not a
username like `@yourname`. Get it from [@userinfobot](https://t.me/userinfobot).
