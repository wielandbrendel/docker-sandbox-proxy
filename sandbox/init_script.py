"""Generate sandbox init scripts for running inside the Docker Sandbox VM.

The sandbox uses a custom template image (sandbox-openclaw:latest) that has
Node 22, pnpm, OpenClaw, and gogcli pre-installed. The init script only
needs to set up env vars, link configs, and start the gateway.
"""

from __future__ import annotations

from sandbox.config.schema import AgentConfig

# Template image with OpenClaw pre-installed
SANDBOX_TEMPLATE = "sandbox-openclaw:latest"


def generate_root_setup_script(config: AgentConfig, agent_dir: str) -> str:
    """Generate script that runs as root for one-time VM configuration."""
    lines = [
        "#!/usr/bin/env bash",
        "set -e",
        "",
    ]

    # Link gogcli config from workspace
    lines.extend([
        "# ── Link gogcli config ──",
        f'GOGCLI_SRC="{agent_dir}/gogcli-config"',
        'GOGCLI_DST="/home/agent/.config/gogcli"',
        'if [ -d "$GOGCLI_SRC" ] && [ ! -e "$GOGCLI_DST" ]; then',
        '    mkdir -p /home/agent/.config',
        '    ln -sfn "$GOGCLI_SRC" "$GOGCLI_DST"',
        '    chown -h agent:agent "$GOGCLI_DST"',
        '    chown -R agent:agent "$GOGCLI_SRC" 2>/dev/null || true',
        '    echo "[root-setup] Linked gogcli config"',
        "fi",
        "",
    ])

    # Copy auth files from workspace to local fs (virtiofs can't handle SQLite)
    lines.extend([
        "# ── Copy OpenClaw auth to local fs ──",
        f'AUTH_SRC="{agent_dir}/openclaw-data/agents/main/agent"',
        'AUTH_DST="/home/agent/.openclaw/agents/main/agent"',
        'if [ -d "$AUTH_SRC" ]; then',
        '    mkdir -p "$AUTH_DST"',
        '    cp -f "$AUTH_SRC"/auth*.json "$AUTH_DST/" 2>/dev/null || true',
        '    chown -R agent:agent /home/agent/.openclaw',
        '    echo "[root-setup] Copied auth files"',
        "fi",
        "",
    ])

    # Copy openclaw.json (always overwrite to pick up config changes)
    lines.extend([
        f'OC_SRC="{agent_dir}/openclaw-data/openclaw.json"',
        'OC_DST="/home/agent/.openclaw/openclaw.json"',
        'if [ -f "$OC_SRC" ]; then',
        '    mkdir -p /home/agent/.openclaw',
        '    cp "$OC_SRC" "$OC_DST"',
        '    chown agent:agent "$OC_DST"',
        '    echo "[root-setup] Copied openclaw.json"',
        "fi",
        "",
        "# ── Symlink cron dir from workspace (persists job state across restarts) ──",
        f'CRON_SRC="{agent_dir}/openclaw-data/cron"',
        'CRON_DST="/home/agent/.openclaw/cron"',
        'if [ -d "$CRON_SRC" ]; then',
        '    mkdir -p /home/agent/.openclaw',
        '    rm -rf "$CRON_DST"',
        '    ln -sfn "$CRON_SRC" "$CRON_DST"',
        '    chown -h agent:agent "$CRON_DST"',
        '    chown -R agent:agent "$CRON_SRC" 2>/dev/null || true',
        '    echo "[root-setup] Linked cron dir ($(ls "$CRON_SRC"/*.json 2>/dev/null | wc -l) job files)"',
        "fi",
        "",
        "# ── Create /workspace symlink (OpenClaw default) ──",
        f'ln -sfn "{agent_dir}/workspace" /workspace 2>/dev/null || true',
        "",
        "# ── Expose Gmail safety wrapper on PATH ──",
        f'if [ -x "{agent_dir}/gmail-tool.sh" ]; then',
        f'    ln -sfn "{agent_dir}/gmail-tool.sh" /usr/local/bin/gmail-tool',
        '    echo "[root-setup] Linked gmail-tool"',
        "fi",
        "",
        "# ── Fix sqlite-vec library path (double .so.so bug) ──",
        'VEC_SO=$(ls /home/agent/.local/share/pnpm/global/5/.pnpm/sqlite-vec-linux-*/node_modules/sqlite-vec-linux-*/vec0.so 2>/dev/null | head -1)',
        'if [ -n "$VEC_SO" ] && [ ! -f "${VEC_SO}.so" ]; then',
        '    ln -sf "$VEC_SO" "${VEC_SO}.so"',
        '    echo "[root-setup] Fixed sqlite-vec library path"',
        'fi',
    ])

    return "\n".join(lines) + "\n"


def generate_init_script(config: AgentConfig, agent_dir: str) -> str:
    """Generate the startup script (runs as agent user via exec -d).

    Uses `exec openclaw gateway` to replace the shell — `docker sandbox
    exec -d` keeps the process alive as a detached process.
    """
    lines = [
        "#!/usr/bin/env bash",
        "set -e",
        "",
        "# ── PATH setup ──",
        'export PATH="/usr/local/bin:/home/agent/.local/share/pnpm/bin:/home/agent/.local/share/pnpm:$PATH"',
        "",
    ]

    # CA cert env vars for Gmail filter
    if config.gmail_filter.enabled:
        cert_path = f"{agent_dir}/gmail-filter-certs/ca-bundle.crt"
        lines.extend([
            "# ── Gmail filter CA trust ──",
            f'export NODE_EXTRA_CA_CERTS="{cert_path}"',
            f'export REQUESTS_CA_BUNDLE="{cert_path}"',
            f'export SSL_CERT_FILE="{cert_path}"',
            f'export CURL_CA_BUNDLE="{cert_path}"',
            'export GOOGLE_API_USE_REST="1"',
            "",
        ])

    # Proxy environment (rely on Node's built-in env-proxy support; do NOT
    # use NODE_OPTIONS=--require proxy-bootstrap.cjs — that can hang OpenClaw
    # at "loading configuration…" because the bootstrap
    # interferes with pnpm child workers used for plugin staging).
    lines.extend([
        "# ── Proxy env (Node's undici reads HTTPS_PROXY/HTTP_PROXY natively) ──",
        'export HTTP_PROXY="http://host.docker.internal:3128"',
        'export HTTPS_PROXY="http://host.docker.internal:3128"',
        'export http_proxy="http://host.docker.internal:3128"',
        'export https_proxy="http://host.docker.internal:3128"',
        'export NO_PROXY="localhost,127.0.0.1,host.docker.internal"',
        'export no_proxy="localhost,127.0.0.1,host.docker.internal"',
        "",
    ])

    # Source .env file
    if config.env_file:
        env_file_path = f"{agent_dir}/{config.env_file}"
        lines.extend([
            "# ── Source .env file ──",
            f'if [ -f "{env_file_path}" ]; then',
            '    set -a',
            f'    . "{env_file_path}"',
            '    set +a',
            'fi',
            "",
        ])

    # Agent env vars (override .env)
    if config.env:
        lines.append("# ── Agent environment ──")
        for key, value in config.env.items():
            lines.append(f'export {key}="{value}"')
        lines.append("")

    # Clean stale state
    lines.extend([
        "# ── Clean stale OpenClaw state ──",
        'rm -f ~/.openclaw/agents/main/agent/models.json 2>/dev/null || true',
        "",
    ])

    # Point workspace to virtiofs
    lines.extend([
        "# ── Set workspace to shared filesystem ──",
        f'export OPENCLAW_WORKSPACE="{agent_dir}/workspace"',
        "",
    ])

    # Start OpenClaw gateway
    port = config.openclaw.port
    lines.extend([
        f"# ── Start OpenClaw gateway on port {port} ──",
        f'echo "[sandbox-init] Starting OpenClaw gateway on port {port}..."',
        f'exec openclaw gateway --port {port} --allow-unconfigured',
    ])

    return "\n".join(lines) + "\n"
