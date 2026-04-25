import typer

from sandbox.commands import config, destroy, init, logs, proxy, ps, restart, shell, start, stop

app = typer.Typer(
    name="sandbox",
    help="Agent sandbox management CLI (v2 — Docker Sandboxes + NanoClaw)",
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
