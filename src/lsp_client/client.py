from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any

from lsp_client.server.base import LSPServerInfo, LSPServerPool, ServerRequestQueue
from lsp_client.types import AnyPath
from lsp_client.utils.path import AbsPath

from .capability.client import LSPCapabilityClientBase


@dataclass
class LSPClientBase[Client: LSPCapabilityClientBase](ABC):
    server_count: int = 1
    server_info: LSPServerInfo = field(default_factory=LSPServerInfo)
    pending_timeout: float = 10
    initialization_options: dict[str, Any] | None = None

    @cached_property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.__name__)

    @asynccontextmanager
    async def start(self, repo_path: AnyPath) -> AsyncGenerator[Client]:
        server_req_queue = ServerRequestQueue()
        async with (
            LSPServerPool.load(
                server_cmd=self.server_cmd,
                server_req_queue=server_req_queue,
                process_count=self.server_count,
                info=self.server_info,
                pending_timeout=self.pending_timeout,
            ) as server,
            self.cap.start(
                repo_path=AbsPath(repo_path),
                server=server,
                initialization_options=self.initialization_options,
            ) as client,
        ):
            yield client

    @property
    @abstractmethod
    def server_cmd(self) -> Sequence[str]:
        """The command to start the LSP server."""

    @property
    @abstractmethod
    def cap(self) -> type[Client]:
        """The capability client class for this LSP client."""
