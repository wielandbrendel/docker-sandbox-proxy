# Telegram Setup

## Create a bot

1. Open Telegram and message [@BotFather](https://t.me/botfather).
2. Send `/newbot`.
3. Choose a display name (can contain spaces).
4. Choose a username (must end in `bot`, e.g. `my_assistant_bot`).
5. BotFather replies with your API token:

   ```
   Done! Congratulations on your new bot.
   ...
   Use this token to access the HTTP API:
   7654321098:BBF_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
   Keep your token secure and store it safely.
   ```

6. Copy that token to `TELEGRAM_BOT_TOKEN` in your `.env`.

To get your numeric user ID (needed for `TELEGRAM_CHAT_ID`), send any message
to [@userinfobot](https://t.me/userinfobot). It replies with your ID.

## Pairing flow

When someone sends a DM to your bot for the first time, OpenClaw holds the
message until you approve the pairing.

1. Send any message to your bot (e.g. "hello").
2. The bot replies:

   ```
   Pairing request from Telegram user 123456789.
   Code: ABC-123
   Approve with: openclaw pairing approve telegram ABC-123
   ```

3. Approve it:

   ```bash
   sandbox shell my-agent
   openclaw pairing approve telegram ABC-123
   exit
   ```

4. The bot immediately processes and replies to your original message.

To reject: `openclaw pairing reject telegram ABC-123`.

## DM allowlist

By default, OpenClaw only accepts messages from approved users. The pairing
approval adds users to this list. If you want to allow a user without going
through the pairing flow (e.g. you know their user ID ahead of time), you can
add it directly to the OpenClaw config inside the sandbox.

The exact config key depends on the OpenClaw version. Check
`~/.openclaw/openclaw.json` inside the sandbox for `allowedSenders` or
similar.

## Group chats

OpenClaw supports group chats if the bot is added to the group. The pairing
flow works the same way — the first message to the bot in the group triggers
the pairing request.

## Privacy mode

By default, Telegram bots in groups only receive messages that directly mention
them (`@botusername`). If you want the bot to read all messages in a group,
disable privacy mode via BotFather:

1. `/mybots` → select your bot → Bot Settings → Group Privacy → Turn off

Note: this applies to new groups the bot joins. Existing groups need to be
re-added or have privacy mode toggled.

## Common errors

### Bot does not respond at all

- Check `sandbox check my-agent` — it calls `/getMe` and verifies the token.
- Check `sandbox logs my-agent` for gateway errors.

### "Pairing code expired"

Pairing codes expire after a few minutes. Have the user send another message
to get a fresh code.

### "Unknown user"

If the user's first message was before pairing was approved and the code was
not used, send another message to get a new code.

### Messages arrive but bot never replies

The agent may be processing but the session delivery is failing. Check:

```bash
sandbox shell my-agent
# look for delivery errors in openclaw logs
```

If `delivery.mode: "announce"` is used in a cron job from an isolated session,
that will fail. See [docs/architecture.md](architecture.md) for the correct
cron pattern.
