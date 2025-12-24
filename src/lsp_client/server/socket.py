from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import final, override

import anyio
from anyio.abc import ByteStream
from anyio.streams.buffered import BufferedByteReceiveStream
from attrs import define, field
from loguru import logger
from tenacity import AsyncRetrying, stop_after_delay, wait_exponential

from lsp_client.jsonrpc.parse import read_raw_package, write_raw_package
from lsp_client.jsonrpc.types import RawPackage
from lsp_client.utils.workspace import Workspace

from .abc import Server


@final
@define
class SocketServer(Server):
    """Runtime for socket backend, e.g. connecting to a remote LSP server via TCP or Unix socket."""

    host: str | None = None
    """The host to connect to (TCP only)."""
    port: int | None = None
    """The port to connect to (TCP only)."""
    path: Path | str | None = None
    """The path to the Unix socket (Unix only)."""
    timeout: float = 10.0
    """Timeout for connecting to the socket."""

    _stream: ByteStream | None = field(init=False, default=None)
    _buffered: BufferedByteReceiveStream | None = field(init=False, default=None)

    @override
    async def check_availability(self) -> None:
        if self.host is None and self.port is None and self.path is None:
            raise ValueError(
                "Either host and port (for TCP), or path (for Unix socket) must be provided"
            )

    @override
    async def send(self, package: RawPackage) -> None:
        if self._stream is None:
            raise RuntimeError(
                "SocketServer is not running. Use 'async with server.run(...)'"
            )
        await write_raw_package(self._stream, package)

    @override
    async def receive(self) -> RawPackage | None:
        if self._buffered is None:
            raise RuntimeError(
                "SocketServer is not running. Use 'async with server.run(...)'"
            )
        try:
            return await read_raw_package(self._buffered)
        except (anyio.EndOfStream, anyio.IncompleteRead, anyio.ClosedResourceError):
            logger.debug("Socket closed")
            return None

    @override
    async def kill(self) -> None:
        if self._stream:
            await self._stream.aclose()

    @override
    @asynccontextmanager
    async def run_process(self, workspace: Workspace) -> AsyncGenerator[None]:
        await self.check_availability()

        async def connect() -> ByteStream:
            if self.host is not None and self.port is not None:
                logger.debug("Connecting to {}:{}", self.host, self.port)
                return await anyio.connect_tcp(self.host, self.port)
            if self.path is not None:
                if not hasattr(anyio, "connect_unix"):
                    raise RuntimeError(
                        "Unix sockets are not supported on this platform"
                    )
                logger.debug("Connecting to {}", self.path)
                return await anyio.connect_unix(str(self.path))
            raise ValueError("Either host and port, or path must be provided")

        stream: ByteStream | None = None
        async for attempt in AsyncRetrying(
            stop=stop_after_delay(self.timeout),
            wait=wait_exponential(multiplier=0.1, max=1),
            reraise=True,
        ):
            with attempt:
                stream = await connect()

        if stream is None:
            raise RuntimeError("Failed to connect to socket")

        async with stream:
            self._stream = stream
            self._buffered = BufferedByteReceiveStream(stream)
            try:
                yield
            finally:
                self._stream = None
                self._buffered = None
