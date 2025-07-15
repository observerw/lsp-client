from __future__ import annotations

from lsp_client.client import LSPClientBase


async def start_mcp(client: LSPClientBase):
    """
    Start a MCP server from existing LSP client.

    This function is useful for customized LSP clients that want to
    integrate with the MCP protocol.
    """

    raise NotImplementedError
