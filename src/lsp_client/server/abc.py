from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Self

import asyncer
from attrs import Factory, define, field
from loguru import logger

from lsp_client.jsonrpc.channel import ResponseTable, response_channel
from lsp_client.jsonrpc.types import (
    RawNotification,
    RawPackage,
    RawRequest,
    RawResponsePackage,
)
from lsp_client.server.types import ServerRequest
from lsp_client.utils.channel import Sender


@define(kw_only=True)
class LSPServer(ABC):
    args: list[str] = Factory(list)

    _resp_table: ResponseTable = field(factory=ResponseTable, init=False)

    @abstractmethod
    async def send(self, package: RawPackage) -> None:
        """Send a package to the runtime."""

    @abstractmethod
    async def receive(self) -> RawPackage | None:
        """Receive a package from the runtime."""

    @abstractmethod
    async def kill(self) -> None:
        """Kill the runtime process."""

    @abstractmethod
    @asynccontextmanager
    def run_process(self) -> AsyncGenerator[None]:
        """Run the server process."""

    async def _dispatch(self, sender: Sender[ServerRequest]) -> None:
        async def handle(package: RawPackage) -> None:
            match package:
                case {"result": _, "id": id} | {"error": _, "id": id} as resp:
                    self._resp_table.send(id, resp)
                case {"id": id, "method": _} as req:
                    tx, rx = response_channel.create()
                    await sender.send((req, tx))
                    resp = await rx.receive()
                    await self.send(resp)
                case {"method": _} as noti:
                    await sender.send(noti)

        async with asyncer.create_task_group() as tg:
            while package := await self.receive():
                tg.soonify(handle)(package)

    async def request(self, request: RawRequest) -> RawResponsePackage:
        await self.send(request)
        return await self._resp_table.receive(request["id"])

    async def notify(self, notification: RawNotification) -> None:
        await self.send(notification)

    @asynccontextmanager
    async def serve(
        self, *, sender: Sender[ServerRequest] | None = None
    ) -> AsyncGenerator[Self]:
        async with (
            self.run_process(),
            asyncer.create_task_group() as tg,
        ):
            if sender:
                tg.soonify(self._dispatch)(sender)
            else:
                logger.debug("Server request sender not provided, skipping dispatch.")

            yield self
