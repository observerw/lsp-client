from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field

from lsp_client.server.stdio import LSPServerInfo, StdioServer

from .base import LSPClientBase


@dataclass
class StdioClient(LSPClientBase):
    """LSP client with stdio server related options."""

    server_count: int | None = 1
    """Count of the server processes."""

    server_info: LSPServerInfo = field(default_factory=LSPServerInfo)
    """Server info."""

    @abstractmethod
    def create_server(self) -> StdioServer:
        """Create a stdio server instance."""


@dataclass
class DockerStdioClient(StdioClient):
    """LSP client with docker support."""

    docker: bool = False
    """Whether to run the lsp server in a docker container."""
