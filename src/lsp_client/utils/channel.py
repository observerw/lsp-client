"""[tokio-like](https://docs.rs/tokio/latest/tokio/sync/index.html) channel utilities."""

from __future__ import annotations

import asyncio as aio
from asyncio import Event
from collections.abc import Hashable
from dataclasses import dataclass, field
from typing import NamedTuple, Self


class DataEvent[T](Event):
    """`asyncio.Event` with data."""

    _data: T | None = None

    def set_data(self, data: T) -> None:
        self._data = data
        self.set()

    def get_data(self) -> T:
        if not self.is_set():
            raise ValueError("DataEvent not set")
        if self._data is None:
            raise ValueError("DataEvent data not set")

        return self._data

    async def wait_data(self) -> T:
        """Wait for data to be set, then return it."""

        await self.wait()
        return self.get_data()


class ManyDataEvent[T](Event):
    expect_count: int
    _data: list[T] | None = None

    def __init__(self, expect_count: int) -> None:
        super().__init__()
        self.expect_count = expect_count
        self._data = []

    def set_data(self, data: T) -> None:
        if self._data is None:
            self._data = []

        self._data.append(data)

        if len(self._data) >= self.expect_count:
            self.set()

    def get_data(self) -> list[T]:
        if not self.is_set():
            raise ValueError("ManyDataEvent not set")
        if self._data is None:
            raise ValueError("ManyDataEvent data not set")

        return self._data

    async def wait_data(self) -> list[T]:
        """Wait for data to be set, then return it."""

        await self.wait()
        return self.get_data()


@dataclass(frozen=True)
class OneShotSender[T]:
    _event: DataEvent[T]

    def send(self, item: T) -> None:
        if self._event.is_set():
            raise RuntimeError("Receiver already closed")

        self._event.set_data(item)

    @property
    def closed(self) -> bool:
        return self._event.is_set()


@dataclass(frozen=True)
class OneShotReceiver[T]:
    _event: DataEvent[T]

    async def receive(self, *, timeout: float | None = None) -> T:
        return await aio.wait_for(self._event.wait_data(), timeout=timeout)

    def try_receive(self) -> T | None:
        if not self._event.is_set():
            return None

        return self._event.get_data()

    def close(self) -> None:
        self._event.set()

    @property
    def closed(self) -> bool:
        return self._event.is_set()


class oneshot_channel[T](NamedTuple):
    sender: OneShotSender[T]
    receiver: OneShotReceiver[T]

    @classmethod
    def create(cls) -> Self:
        event = DataEvent[T]()
        sender = OneShotSender[T](_event=event)
        receiver = OneShotReceiver[T](_event=event)
        return cls(sender=sender, receiver=receiver)


@dataclass(frozen=True)
class ManyShotSender[T]:
    _event: ManyDataEvent[T]

    def send(self, item: T) -> None:
        if self._event.is_set():
            raise RuntimeError("ManyShotSender can only be used once")
        self._event.set_data(item)

    @property
    def closed(self) -> bool:
        return self._event.is_set()


@dataclass(frozen=True)
class ManyShotReceiver[T]:
    _event: ManyDataEvent[T]

    async def receive(self, *, timeout: float | None = None) -> list[T]:
        return await aio.wait_for(self._event.wait_data(), timeout=timeout)

    def try_receive(self) -> list[T] | None:
        if not self._event.is_set():
            return None

        return self._event.get_data()

    @property
    def closed(self) -> bool:
        return self._event.is_set()


class manyshot_channel[T](NamedTuple):
    sender: ManyShotSender[T]
    receiver: ManyShotReceiver[T]

    @classmethod
    def create(cls, expect_count: int) -> Self:
        """Create a many-shot channel."""
        event = ManyDataEvent[T](expect_count=expect_count)
        sender = ManyShotSender[T](_event=event)
        receiver = ManyShotReceiver[T](_event=event)
        return cls(sender=sender, receiver=receiver)


type ShotSender[T] = OneShotSender[T] | ManyShotSender[T]
type ShotReceiver[T] = OneShotReceiver[T] | ManyShotReceiver[T]


@dataclass(frozen=True)
class ShotTable[T]:
    """Dispatch data to one-shot senders by ID."""

    _pending: dict[Hashable, ShotSender[T]] = field(default_factory=dict)
    _empty_cond: aio.Condition = field(default_factory=aio.Condition)
    """Condition variable to wait for _pending to be empty."""

    async def register(self, id: Hashable, sender: ShotSender[T]) -> None:
        """Register a one-shot sender with an ID."""

        if id in self._pending:
            raise ValueError(f"Sender with id {id} already registered")

        async with self._empty_cond:
            self._pending[id] = sender

    async def send(self, id: Hashable, data: T) -> None:
        if id not in self._pending:
            raise ValueError(f"Pending request of id {id} not found")

        self._pending[id].send(data)

        async with self._empty_cond:
            self._pending.pop(id)
            if self._pending:
                return
            self._empty_cond.notify_all()

    async def wait(self, id: Hashable) -> T:
        tx, rx = oneshot_channel.create()

        try:
            await self.register(id, tx)
            return await rx.receive()
        finally:
            self._pending.pop(id, None)

    async def wait_many(self, id: Hashable, expect_count: int) -> list[T]:
        tx, rx = manyshot_channel.create(expect_count=expect_count)

        try:
            await self.register(id, tx)
            return await rx.receive()
        finally:
            self._pending.pop(id, None)

    async def wait_complete(self) -> None:
        async with self._empty_cond:
            while self._pending:
                await self._empty_cond.wait()

    @property
    def completed(self) -> bool:
        return not self._pending
