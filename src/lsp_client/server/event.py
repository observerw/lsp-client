from __future__ import annotations

import asyncio as aio
import logging
from asyncio import Event
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import override

from lsp_client.jsonrpc import JsonRpcID, JsonRpcRawRespPackage

logger = logging.getLogger(__name__)


class DataEvent[T](Event):
    """`asyncio.Event` with data."""

    data: T | None = None

    def set_data(self, data: T) -> None:
        self.data = data
        self.set()

    def get_data(self) -> T:
        """Get data immediately, or raise ValueError if data is not set."""

        if not self.is_set():
            raise ValueError("DataEvent not set")
        if self.data is None:
            raise ValueError("DataEvent data not set")

        return self.data


class RequestEventBase[T](DataEvent[T]):
    id: JsonRpcID
    method: str  # for debugging purposes

    def __init__(self, id: JsonRpcID, method: str):
        super().__init__()
        self.id = id
        self.method = method

    @override
    def set_data(self, data: T) -> None:
        return super().set_data(data)


class SingleRequestEvent(RequestEventBase[JsonRpcRawRespPackage]):
    """For `client.request`"""


class BatchRequestEvent(RequestEventBase[list[JsonRpcRawRespPackage]]):
    """For `client.request_all`"""

    expected_count: int

    def __init__(
        self,
        id: JsonRpcID,
        method: str,
        expected_count: int,
    ):
        super().__init__(id=id, method=method)
        self.expected_count = expected_count

    def append_data(self, response: JsonRpcRawRespPackage) -> None:
        if not self.data:
            self.data = []

        self.data.append(response)

        if len(self.data) == self.expected_count:
            self.set()


type RequestEvent = SingleRequestEvent | BatchRequestEvent


@dataclass
class RequestManager:
    timeout: float | None = 5.0

    _cond: aio.Condition = field(default_factory=aio.Condition)
    _pending: dict[JsonRpcID, RequestEvent] = field(default_factory=dict)

    async def wait_complete(self):
        async with self._cond:
            while len(self._pending) > 0:
                await self._cond.wait()

    @asynccontextmanager
    async def request[T: RequestEvent](self, event: T) -> AsyncGenerator[T]:
        try:
            self._pending[event.id] = event
            yield event
            await aio.wait_for(event.wait(), timeout=self.timeout)
            assert event.is_set(), "Event not set after waiting"
            assert event.data is not None, "Event data not set"
        finally:
            async with self._cond:
                self._pending.pop(event.id, None)
                self._cond.notify_all()

    async def respond(self, resp: JsonRpcRawRespPackage):
        """Respond to a request with the given id."""

        id = resp["id"]
        assert id, f"Unexpected response without id: {resp}"

        assert id in self._pending, (
            f"Response {resp} with id {id} not found in pending requests"
        )

        match self._pending[id]:
            case SingleRequestEvent() as event:
                event.set_data(resp)
            case BatchRequestEvent() as event:
                event.append_data(resp)
            case _:
                raise ValueError(f"Unknown request event type for id {id}")
