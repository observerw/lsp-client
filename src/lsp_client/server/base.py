from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Self

from lsp_client import jsonrpc
from lsp_client.types import Workspace


@dataclass(kw_only=True)
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

    @property
    @abstractmethod
    def server_request_receiver(self) -> jsonrpc.ReqReceiver: ...

    @asynccontextmanager
    @abstractmethod
    def serve(self, workspace: Workspace) -> AsyncGenerator[Self]: ...
