# Architecture

docker-sandbox-proxy runs AI agents inside Docker Desktop Sandbox VMs with
deny-by-default network access and, optionally, an operation-level Gmail MITM
filter that blocks send/delete operations while allowing reads.

## Overview

Docker Desktop Sandbox provides each agent with a lightweight VM and a
transparent HTTPS proxy. This project layers additional controls on top:

- A DNS and HTTPS proxy allowlist so agents can only reach explicitly approved
  domains
- An optional Gmail filter sidecar that intercepts Gmail API calls and
  rejects anything that mutates data (send, delete, settings changes)
- An idempotent keepalive daemon so the VM does not sleep on macOS

## Network diagram

```
  ┌─────────────────────────────────────────────────────────────┐
  │  Docker Sandbox VM                                          │
  │                                                             │
  │   ┌─────────────────────┐                                  │
  │   │  agent container    │  (non-root, no capabilities)     │
  │   │  openclaw gateway   │                                  │
  │   └────────┬────────────┘                                  │
  │            │ all traffic                                   │
  │            ▼                                               │
  │   ┌────────────────────┐                                   │
  │   │  Docker Sandbox    │  DNS allow-list + HTTPS proxy     │
  │   │  transparent proxy │  (deny by default)                │
  │   └────────┬───────────┘                                   │
  │            │                                               │
  └────────────┼────────────────────────────────────────────── ┘
               │
       ┌───────┴────────────────────────────┐
       │                                    │
       ▼ (if gmail_filter.enabled)          ▼
  ┌─────────────────┐               ┌────────────────┐
  │  gmail-filter   │               │  Internet       │
  │  (host, Docker) │               │  (allowlisted   │
  │  OpenResty+Lua  │               │   domains only) │
  └─────────────────┘               └────────────────┘
```

The agent container has no special Linux capabilities (`cap_drop: ALL`,
`no-new-privileges: true`) so it cannot modify its own proxy rules.

## Five security layers

### Layer 1: DNS (Docker Sandbox proxy)

Docker Desktop Sandbox includes a transparent DNS proxy. When
`network.policy: deny`, only domains in `network.allow` (in `agent.yaml`)
resolve. Everything else returns NXDOMAIN. This prevents DNS-tunneling and
accidental access to non-allowlisted services.

### Layer 2: HTTPS proxy (Docker Sandbox proxy)

The same proxy enforces the allowlist at the TLS layer. Even if an agent
hardcoded an IP address, the proxy would block the connection if the domain
is not whitelisted. All outbound TCP port 443 goes through it.

Some clients (npm, Telegram bot SDK) have issues with the MITM proxy. These
are configured as `bypass_hosts` in `start.py` — they bypass the proxy
transparently but still route only to allowlisted IPs.

### Layer 3: Gmail filter (optional)

When `gmail_filter.enabled: true`, an OpenResty + Lua container runs on the
host. The Docker Sandbox proxy configuration redirects Gmail API traffic to
this container instead of the public internet.

The filter performs HTTPS MITM using a locally-generated CA. The CA cert is
injected into the agent via `NODE_EXTRA_CA_CERTS`, `REQUESTS_CA_BUNDLE`,
`SSL_CERT_FILE`, and `CURL_CA_BUNDLE`. The agent's TLS stack trusts the filter
and the filter proxies to the real Gmail API.

Every request is URI-canonicalized (percent-decode, null-byte check,
double-encoding rejection, path normalization) then matched against an
allowlist. Anything not on the allowlist returns 403.

See [docs/gmail-filter.md](gmail-filter.md) for the full allowlist.

### Layer 4: Kernel firewall (Docker Sandbox VM)

The Docker Desktop Sandbox VM runs its own iptables rules. The project
configures these via `docker sandbox proxy` — outbound connections that don't
match an allowlisted domain are dropped at the kernel level. This is the
enforcement point that makes the proxy rules immutable from inside the agent.

### Layer 5: Process isolation

- Non-root user (`1000:1000`)
- `cap_drop: [ALL]` — no Linux capabilities
- `no-new-privileges: true` — cannot escalate via setuid/setgid
- Configurable CPU and memory limits

## VM lifecycle and keepalive

Docker Desktop Sandbox VMs on macOS stop after ~15 minutes of idle (no exec
calls). When the VM is stopped, the agent is unreachable.

The keepalive daemon (`scripts/install-keepalive.sh`) installs a launchd plist
that runs every 2 minutes. It calls `docker sandbox exec` on each running
sandbox, which is enough to prevent idle-sleep.

**macOS TCC note:** The daemon must run from `~/.local/bin/`, not from
`~/Documents/`. macOS TCC (Transparency, Consent, Control) blocks launchd
services in user home subdirectories from accessing Documents. The installer
handles this automatically.

The plist uses `StartCalendarInterval` (explicit minute list) rather than
`StartInterval`. The macOS launchd throttles `StartInterval` jobs when the
system is idle, which defeats the purpose.

## OpenClaw and cron

OpenClaw runs as a gateway process inside the sandbox. It handles:
- LLM API calls (routed through the proxy allowlist)
- Telegram bot polling
- Cron job scheduling (`~/.openclaw/cron/jobs.json`)

Cron jobs that need to deliver a result to Telegram should use
`sessionTarget: "isolated"` + `payload.kind: "agentTurn"` with
`delivery.mode: "none"`, and have the agent explicitly announce to the main
session. See CLAUDE.md in this repo for details on the cron delivery
constraints.
