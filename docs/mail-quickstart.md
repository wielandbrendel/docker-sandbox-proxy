# Mail Quickstart

Linear walkthrough: from a clean checkout to your first Telegram reply in
~15 minutes. This covers everything in
[sandboxes/example-mail/README.md](../sandboxes/example-mail/README.md)
plus expected output at each step so you know it's working.

## Prerequisites

- Completed [quickstart.md](quickstart.md) (base image built, `sandbox` CLI works)
- A Telegram account
- A Google account with Gmail

## Step 1: Copy the example

```bash
bash scripts/new-agent.sh my-mail --mail
```

Expected:

```
Copied example-mail → sandboxes/my-mail
Created sandboxes/my-mail
  Gmail filter HTTPS port: 8443
  Gmail filter HTTP port: 8080
  Edit agent.yaml to configure, then run: sandbox start my-mail
```

## Step 2: Get a Telegram bot token

1. Open Telegram, message [@BotFather](https://t.me/botfather).
2. Send `/newbot`, choose a name and a username (must end in `bot`).
3. BotFather replies:

   ```
   Done! Congratulations on your new bot. You will find it at t.me/YourBotName.
   Use this token to access the HTTP API:
   1234567890:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   Keep your token secure...
   ```

4. Copy that token.
5. Get your numeric Telegram user ID from [@userinfobot](https://t.me/userinfobot)
   (just send it a message; it replies with your ID).

## Step 3: Set up Google OAuth for Gmail

Run the setup wizard:

```bash
bash scripts/setup-gog.sh
```

This installs `gogcli` (Google OAuth gateway CLI) and walks you through
creating a Google Cloud project with the Gmail API enabled.

Then authenticate:

```bash
gog auth manage
```

Pick "add account" — a browser window opens. Authorise the app for your Gmail
account. When done, the terminal shows:

```
Account added: you@example.com
```

Note the account identifier (usually the email address). You'll need it as
`GOG_ACCOUNT` in `.env`.

## Step 4: Fill in .env

```bash
cd sandboxes/my-mail
cp .env.example .env
```

Open `.env` and fill in:

```bash
TELEGRAM_BOT_TOKEN=1234567890:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=123456789           # your numeric user ID
GOG_ACCOUNT=you@example.com          # from gog auth manage
```

Save and close.

## Step 5: Preflight check

```bash
sandbox check my-mail
```

Expected (all green):

```
[OK] .env file: sandboxes/my-mail/.env
[OK] required env vars: all set
[OK] base image sandbox-template:latest: present
[OK] telegram getMe: @YourBotName
4 passed, 0 failed
```

If any line shows `[FAIL]`, read the `fix:` hint. Common issues:
- `FAIL telegram getMe: API call failed` — wrong token; copy it again from BotFather
- `FAIL required env vars: missing: TELEGRAM_CHAT_ID` — fill in the numeric ID, not the username

## Step 6: Start the sandbox

```bash
sandbox start my-mail
```

Expected:

```
Starting gmail-filter (HTTP:8080, HTTPS:8443)...
  gmail-filter healthy.
Creating Docker Sandbox 'my-mail'...
  Sandbox created.
Configuring network proxy...
  Policy: deny, 16 allowed, 3 blocked.
Running root setup...
  [root-setup] linked openclaw config
  [root-setup] copied gogcli credentials
Waiting for OpenClaw to start via entrypoint...
  OpenClaw running (PID 42)
Agent 'my-mail' started.
```

The `3 blocked` are the direct Gmail API hostnames that must go through the
filter (`gmail.googleapis.com`, `content-gmail.googleapis.com`,
`www.googleapis.com`).

## Step 7: Onboard OpenClaw

```bash
sandbox shell my-mail
```

Inside the sandbox:

```
openclaw onboard
```

When prompted for a provider, pick `openai-codex` (OAuth flow — requires a
Codex subscription) or another provider. Complete the prompts. Then:

```
exit
```

## Step 8: Pair Telegram

Send any message to your bot in Telegram. The bot replies with a pairing code:

```
Pairing request from Telegram user 123456789.
Code: ABC-123
Approve with: openclaw pairing approve telegram ABC-123
```

Back in your terminal:

```bash
sandbox shell my-mail
openclaw pairing approve telegram ABC-123
exit
```

## Step 9: Verify

Send another message to your bot. It should reply. Then:

```bash
sandbox ps
```

Expected:

```
NAME      STATUS    OPENCLAW PORT
my-mail   running   18789
```

Check agent logs if there's no response:

```bash
sandbox logs my-mail
```

## What success looks like

- The bot replies to your Telegram messages.
- The agent can read your Gmail (`gog gmail list` inside the sandbox works).
- The agent cannot send email (any attempt is blocked with 403 by the Gmail
  filter — see [docs/gmail-filter.md](gmail-filter.md)).

## Next steps

- [docs/customizing.md](customizing.md) — adjust the network allowlist, add tools
- [docs/troubleshooting.md](troubleshooting.md) — if the bot stops responding
- [docs/gmail-filter.md](gmail-filter.md) — how the send-blocking works
