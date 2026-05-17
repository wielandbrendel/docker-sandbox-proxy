from sandbox.config.schema import AgentConfig
from sandbox.init_script import generate_init_script, generate_root_setup_script


def test_init_script_sets_pnpm_bin_path():
    script = generate_init_script(AgentConfig(name="test-agent"), "/agents/test-agent")

    assert (
        'export PATH="/usr/local/bin:/home/agent/.local/share/pnpm/bin:'
        '/home/agent/.local/share/pnpm:$PATH"'
    ) in script


def test_init_script_uses_proxy_env_not_node_options():
    script = generate_init_script(AgentConfig(name="test-agent"), "/agents/test-agent")

    assert 'export HTTP_PROXY="http://host.docker.internal:3128"' in script
    assert 'export HTTPS_PROXY="http://host.docker.internal:3128"' in script
    assert 'export NO_PROXY="localhost,127.0.0.1,host.docker.internal"' in script
    assert "NODE_OPTIONS" not in script
    assert "proxy-bootstrap.cjs" not in script


def test_root_setup_links_gmail_tool_when_present():
    script = generate_root_setup_script(AgentConfig(name="test-agent"), "/agents/test-agent")

    assert 'if [ -x "/agents/test-agent/gmail-tool.sh" ]; then' in script
    assert 'ln -sfn "/agents/test-agent/gmail-tool.sh" /usr/local/bin/gmail-tool' in script
    assert '[root-setup] Linked gmail-tool' in script


def test_root_setup_links_cron_dir():
    script = generate_root_setup_script(AgentConfig(name="test-agent"), "/agents/test-agent")

    assert 'CRON_SRC="/agents/test-agent/openclaw-data/cron"' in script
    assert 'CRON_DST="/home/agent/.openclaw/cron"' in script
    assert "[root-setup] Linked cron dir" in script
