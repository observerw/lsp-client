from __future__ import annotations

import asyncio
import socket
import time

import typer
from rich.console import Console
from rich.table import Table

from lsp_client.cli.daemon import (
    SOCKET_PATH,
    CreateParams,
    DaemonRequest,
    DaemonResponse,
    ListParams,
    StopParams,
    start_daemon,
)

app = typer.Typer(help="Manage LSP servers")
console = Console()


def ensure_daemon():
    """Ensure the daemon is running."""
    if not SOCKET_PATH.exists():
        start_daemon()
        # Give it a moment to start
        for _ in range(10):
            if SOCKET_PATH.exists():
                break
            time.sleep(0.1)

    # Try to connect to verify it's responsive
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            s.connect(str(SOCKET_PATH))
    except (TimeoutError, ConnectionRefusedError):
        if SOCKET_PATH.exists():
            SOCKET_PATH.unlink()
        start_daemon()
        for _ in range(10):
            if SOCKET_PATH.exists():
                break
            time.sleep(0.1)


async def send_command(request: DaemonRequest) -> DaemonResponse:
    """Send a command to the daemon and return the response."""
    ensure_daemon()

    reader, writer = await asyncio.open_unix_connection(str(SOCKET_PATH))
    try:
        writer.write(request.model_dump_json().encode())
        await writer.drain()

        data = await reader.read(4096)
        if not data:
            return DaemonResponse(status="error", message="No response from daemon")

        return DaemonResponse.model_validate_json(data.decode())
    finally:
        writer.close()
        await writer.wait_closed()


@app.command()
def create(
    name: str = typer.Argument(..., help="Name of the server instance"),
    image: str = typer.Argument(..., help="Docker image to use"),
):
    """Create a new LSP server instance."""
    request = DaemonRequest(
        command="create", params=CreateParams(name=name, image=image)
    )
    response = asyncio.run(send_command(request))
    if response.status == "success":
        console.print(f"[green]{response.message}[/green]")
    else:
        console.print(f"[red]Error: {response.message}[/red]")


@app.command(name="list")
def list_servers():
    """List all running LSP server instances."""
    request = DaemonRequest(command="list", params=ListParams())
    response = asyncio.run(send_command(request))
    if response.status == "success":
        servers = response.servers or {}
        if not servers:
            console.print("No servers running.")
            return

        table = Table(title="LSP Servers")
        table.add_column("Name", style="cyan")
        table.add_column("Image", style="magenta")
        table.add_column("Status", style="green")

        for name, info in servers.items():
            table.add_row(name, info.image, info.status)

        console.print(table)
    else:
        console.print(f"[red]Error: {response.message}[/red]")


@app.command()
def stop(
    name: str = typer.Argument(..., help="Name of the server instance to stop"),
):
    """Stop an LSP server instance."""
    request = DaemonRequest(command="stop", params=StopParams(name=name))
    response = asyncio.run(send_command(request))
    if response.status == "success":
        console.print(f"[green]{response.message}[/green]")
    else:
        console.print(f"[red]Error: {response.message}[/red]")


if __name__ == "__main__":
    app()
