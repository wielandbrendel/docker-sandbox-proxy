import typer

from sandbox.commands import (
    check as check_cmd,
    config,
    destroy,
    init,
    logs,
    proxy,
    ps,
    restart,
    shell,
    start,
    stop,
)

app = typer.Typer(
    name="sandbox",
    help="Docker-Sandbox-isolated AI agent management CLI",
    no_args_is_help=True,
)

app.command()(init.init)
app.command()(start.start)
app.command()(stop.stop)
app.command()(restart.restart)
app.command()(ps.ps)
app.command()(logs.logs)
app.command()(shell.shell)
app.command()(destroy.destroy)
app.command()(config.config)
app.command()(proxy.proxy)
app.command("check")(check_cmd.check)
