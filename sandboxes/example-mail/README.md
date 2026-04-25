# example-mail

Sandboxed OpenClaw agent with operation-filtered Gmail and Telegram.

The Gmail filter blocks send/delete operations at the API layer — the agent
can read mail, draft responses, and archive, but cannot actually send email
or delete anything permanently. See [docs/gmail-filter.md](../../docs/gmail-filter.md).

## Quickstart (~15 minutes from a clean checkout)

This is the linear setup. Each step is verified.

### Step 1: Create your copy

```
bash scripts/new-agent.sh my-mail --mail
cd sandboxes/my-mail
```

### Step 2: Get a Telegram bot token

1. Open Telegram, message [@BotFather](https://t.me/botfather).
2. `/newbot` then pick a name and username.
3. BotFather replies with `Use this token to access the HTTP API: <TOKEN>`. Copy it.
4. Get your numeric user ID from [@userinfobot](https://t.me/userinfobot).

### Step 3: Set up Google OAuth for Gmail

```
bash scripts/setup-gog.sh
```

Follow its prompts, then:

```
gog auth manage
```

Pick "add account" → browser opens → authorize → done.

### Step 4: Fill in .env

```
cp .env.example .env
# edit .env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GOG_ACCOUNT
```

### Step 5: Verify

```
sandbox check my-mail
```

Every line should be ✅. Fix any ❌ before proceeding.

### Step 6: Start the sandbox

```
sandbox start my-mail
```

### Step 7: Onboard OpenClaw

```
sandbox shell my-mail
# inside the sandbox:
openclaw onboard
# follow prompts; pick openai-codex if you have a Codex subscription
exit
```

### Step 8: Pair Telegram

In Telegram, send any message to your bot. It replies with a pairing code.

```
sandbox shell my-mail
openclaw pairing approve telegram <CODE>
exit
```

The bot now responds in Telegram.

## What this sandbox can and can't do

- ✅ Read all Gmail (full message bodies, labels, threads)
- ✅ Create and update drafts
- ✅ Archive messages
- ✅ Send and receive Telegram messages
- ✅ Use OpenAI / GitHub / npm / pypi (allowlisted domains)

- ❌ Send Gmail or actual email
- ❌ Permanently delete Gmail messages or threads
- ❌ Reach any non-allowlisted domain

## Troubleshooting

See [docs/troubleshooting.md](../../docs/troubleshooting.md). Common issues:
- "OAuth token refresh failed for openai-codex" → re-run `openclaw onboard --auth-choice openai-codex`
- "VM stopped, no responses for hours" → install keepalive: `bash scripts/install-keepalive.sh`
- "agent never sends dailies" → check `~/.openclaw/cron/jobs.json` inside the sandbox
