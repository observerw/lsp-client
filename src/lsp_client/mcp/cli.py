from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mcp.server.fastmcp import Context, FastMCP
from typer import Typer

from lsp_client import LSPClientBase, lsp_cap

from .locate import Locate

app = Typer(name="lsp-client")


@dataclass
class AppContext:
    repo_path: Path
    client: LSPClientBase


def lifespan_context(context: Context) -> AppContext:
    context = context.request_context.lifespan_context
    assert isinstance(context, AppContext), "Expected AppContext"
    return context


mcp = FastMCP("lsp-client")


@mcp.tool()
async def requet_reference(loc: Locate, ctx: Context):
    client = lifespan_context(ctx).client
    assert isinstance(client, lsp_cap.WithRequestReferences), (
        "Client must support request references"
    )
    repo_path = lifespan_context(ctx).repo_path
    position = loc.resolve(repo_path)

    return await client.request_references(
        file_path=loc.rel_file_path,
        position=position,
    )


def main():
    mcp.run()
