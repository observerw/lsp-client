from __future__ import annotations

import asyncio as aio
from asyncio import Event
from collections.abc import AsyncGenerator, Hashable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import NamedTuple, Self


class DataEvent[T](Event):
    """`asyncio.Event` with data."""

    _data: T | None = None

    def set_data(self, data: T) -> None:
        self._data = data
        self.set()

    def get_data(self) -> T:
        """Get data immediately, or raise ValueError if data is not set."""

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
        """Get data immediately, or raise ValueError if data is not set."""

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
            raise RuntimeError("OneShotSender can only be used once")
        self._event.set_data(item)

    @property
    def closed(self) -> bool:
        return self._event.is_set()


@dataclass(frozen=True)
class OneShotReceiver[T]:
    _event: DataEvent[T]

    async def receive(self) -> T:
        return await self._event.wait_data()

    def try_receive(self) -> T | None:
        if not self._event.is_set():
            return None

        return self._event.get_data()

    @property
    def closed(self) -> bool:
        return self._event.is_set()


class oneshot_channel[T](NamedTuple):
    sender: OneShotSender[T]
    receiver: OneShotReceiver[T]

    @classmethod
    def create(cls) -> Self:
        """Create a one-shot channel."""
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

    async def receive(self) -> list[T]:
        return await self._event.wait_data()

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

    timeout: float | None = None

    _cond: aio.Condition = field(default_factory=aio.Condition)
    _pending: dict[Hashable, ShotSender[T]] = field(default_factory=dict)

    async def register(self, id: Hashable, sender: ShotSender[T]) -> None:
        """Register a one-shot sender with an ID."""

        if id in self._pending:
            raise ValueError(f"Sender with id {id} already registered")

        async with self._cond:
            self._pending[id] = sender

    async def send(self, id: Hashable, data: T) -> None:
        """Send data through the one-shot sender with the given ID."""
        if id not in self._pending:
            raise ValueError(f"OneShotSender with id {id} not found")

        sender = self._pending[id]

        if sender.closed:
            raise ValueError(f"OneShotSender with id {id} is closed")

        sender.send(data)

        async with self._cond:
            if sender.closed:
                self._pending.pop(id)
                self._cond.notify_all()

    async def wait_complete(self) -> None:
        """Wait until all pending one-shot senders are resolved."""
        async with self._cond:
            while self._pending:
                await self._cond.wait()


@dataclass(frozen=True)
class Sender[T]:
    """MPSC sender"""

    _queue: aio.Queue[T]

    async def send(self, item: T) -> None:
        await self._queue.put(item)


@dataclass(frozen=True)
class Receiver[T]:
    """MPSC receiver"""

    _queue: aio.Queue[T]

    @asynccontextmanager
    async def handle(self) -> AsyncGenerator[T]:
        try:
            yield await self._queue.get()
        finally:
            self._queue.task_done()

    async def receive(self) -> T:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()

    async def join(self) -> None:
        """Wait until all received items have been processed."""
        await self._queue.join()


class channel[T](NamedTuple):
    """MPSC channel"""

    sender: Sender[T]
    receiver: Receiver[T]

    @classmethod
    def create(cls, buffer_size: int = 0) -> channel[T]:
        """Create a channel with a specified buffer size."""

        queue = aio.Queue[T](buffer_size)
        sender = Sender[T](_queue=queue)
        receiver = Receiver[T](_queue=queue)
        return cls(sender=sender, receiver=receiver)
