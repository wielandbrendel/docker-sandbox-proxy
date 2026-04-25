# docker-sandbox-proxy

Sandboxed AI agents using Docker Desktop Sandbox, OpenClaw, and a multi-layer
network policy. Agents live in isolated VMs with deny-by-default internet
access, and an optional operation-level Gmail filter that allows reading mail
without ever being able to send it.

## Why

Running an AI agent with access to your email, GitHub, or other services
requires real isolation — not just "trust the model". A mis-behaving or
compromised agent should not be able to send email, call unexpected APIs, or
exfiltrate data. This project enforces isolation at five independent layers:
DNS resolution, an HTTPS proxy, a per-operation Gmail filter, the kernel
firewall in the Docker Sandbox VM, and non-root process isolation.

None of those layers are bypassable from inside the agent container.

## Quickstart (~5 minutes)

**Prerequisites:** macOS with Docker Desktop 4.40+, Python 3.12+, ~10 GB free.

```bash
git clone https://github.com/wielandbrendel/docker-sandbox-proxy
cd docker-sandbox-proxy
python -m venv .venv && source .venv/bin/activate
pip install -e .
sandbox --help
```

Build the base image (once):

```bash
docker build -t sandbox-template:latest base-image/sandbox-template/
```

(Optional) Install the keepalive daemon so the Docker VM does not sleep after
15 minutes of inactivity:

```bash
bash scripts/install-keepalive.sh
```

Create and start a minimal agent:

```bash
bash scripts/new-agent.sh hello
sandbox start hello
```

Onboard OpenClaw inside the sandbox:

```bash
sandbox shell hello
# inside the sandbox:
openclaw onboard
exit
```

Verify:

```bash
sandbox ps
```

See [docs/quickstart.md](docs/quickstart.md) for the full walkthrough with
expected outputs and verification steps.

## Mail agent (~15 more minutes)

The `example-mail` sandbox adds Gmail read-only access and a Telegram bot.
See [docs/mail-quickstart.md](docs/mail-quickstart.md) for the linear setup.

## Architecture

[docs/architecture.md](docs/architecture.md) — five security layers, VM
lifecycle, proxy quirks, and how the optional Gmail MITM filter works.

## Documentation

| Doc | Contents |
|---|---|
| [docs/quickstart.md](docs/quickstart.md) | Clone → working sandbox in 5 min |
| [docs/mail-quickstart.md](docs/mail-quickstart.md) | Full Gmail + Telegram setup |
| [docs/architecture.md](docs/architecture.md) | Security model and architecture |
| [docs/customizing.md](docs/customizing.md) | Add your own agent |
| [docs/gmail-filter.md](docs/gmail-filter.md) | Optional Gmail operation filter |
| [docs/telegram.md](docs/telegram.md) | Telegram bot setup and pairing |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common issues and fixes |
| [docs/reference/agent-yaml.md](docs/reference/agent-yaml.md) | agent.yaml field reference |
| [docs/reference/cli.md](docs/reference/cli.md) | CLI command reference |

## License

MIT — see [LICENSE](LICENSE).
