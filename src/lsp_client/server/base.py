from __future__ import annotations

import asyncio as aio
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from typing import Self

from lsp_client import jsonrpc
from lsp_client.types import Workspace

ServerRequest = tuple[jsonrpc.RawRequest, jsonrpc.RespSender] | jsonrpc.RawNotification


class LSPServerBase(ABC):
    @abstractmethod
    async def request(
        self, request: jsonrpc.RawRequest
    ) -> jsonrpc.RawResponsePackage: ...

    @abstractmethod
    async def request_all(
        self, request: jsonrpc.RawRequest
    ) -> Sequence[jsonrpc.RawResponsePackage]: ...

    @abstractmethod
    async def notify(self, notification: jsonrpc.RawNotification) -> None: ...

    @property
    @abstractmethod
    def server_request_queue(self) -> aio.Queue[ServerRequest]: ...

    @asynccontextmanager
    @abstractmethod
    def run(self) -> AsyncGenerator[Self]: ...

    @asynccontextmanager
    @abstractmethod
    def serve(self, workspace: Workspace) -> AsyncGenerator[Self]:
        """After `initialize`, before `exit`."""
