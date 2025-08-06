from __future__ import annotations

from dataclasses import dataclass, field

from lsp_client.server.stdio import LSPServerInfo

from .base import LSPClientBase


@dataclass
class StdioClient(LSPClientBase):
    server_count: int | None = 1
    """Count of the server processes."""

    server_info: LSPServerInfo = field(default_factory=LSPServerInfo)
    """Server info."""
