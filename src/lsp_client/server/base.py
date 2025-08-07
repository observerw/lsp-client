from __future__ import annotations

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
        self, requests: jsonrpc.RawRequest
    ) -> Sequence[jsonrpc.RawResponsePackage]: ...

    @abstractmethod
    async def notify(self, notification: jsonrpc.RawNotification) -> None: ...

    @abstractmethod
    async def receive(self) -> ServerRequest | None: ...

    @asynccontextmanager
    @abstractmethod
    def serve(self, workspace: Workspace) -> AsyncGenerator[Self]: ...
