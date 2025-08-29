from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from functools import cached_property
from pathlib import Path
from typing import Any, Self

import anyio
from anyio.abc import ByteSendStream, Process
from anyio.streams.buffered import BufferedByteReceiveStream
from attrs import define, field, frozen
from loguru import logger

from lsp_client import jsonrpc
from lsp_client.server.type import ServerRequest
from lsp_client.utils.channel import Sender

from .jsonrpc import read_raw_package, write_raw_package


@frozen
class ProcessConfig:
    cwd: Path = field(default=Path.cwd())
    env: dict[str, Any] | None = None


@define
class LSPStdioProcess(anyio.AsyncContextManagerMixin):
    cmd: Sequence[str]
    config: ProcessConfig

    _process: Process = field(init=False)

    @property
    def stdin(self) -> ByteSendStream:
        stdin = self._process.stdin
        assert stdin, "Process stdin is not available"
        return stdin

    @cached_property
    def stdout(self) -> BufferedByteReceiveStream:
        stdout = self._process.stdout
        assert stdout, "Process stdout is not available"
        return BufferedByteReceiveStream(stdout)

    @cached_property
    def stderr(self) -> BufferedByteReceiveStream:
        stderr = self._process.stderr
        assert stderr, "Process stderr is not available"
        return BufferedByteReceiveStream(stderr)

    async def send(self, package: jsonrpc.RawPackage) -> None:
        await write_raw_package(self.stdin, package)
        logger.debug("Package sent: {}", package)

    async def receive(self) -> jsonrpc.RawPackage | None:
        try:
            package = await read_raw_package(self.stdout)
            logger.debug("Received package: {}", package)
            return package
        except (anyio.EndOfStream, anyio.IncompleteRead):
            logger.debug("Process stdout closed")
            return None

    async def shutdown(self) -> int:
        try:
            # returncode = await aio.wait_for(self.process.wait(), timeout=5.0)
            with anyio.fail_after(5.0):
                returncode = await self._process.wait()
            logger.debug("Process exited with code {}", returncode)
            return returncode
        except TimeoutError:
            logger.warning("Process shutdown timeout reached, killing process")
            await self._process.aclose()
            return 1

    @asynccontextmanager
    async def __asynccontextmanager__(self) -> AsyncGenerator[Self]:
        self._process = await anyio.open_process(
            command=self.cmd,
            cwd=self.config.cwd,
            env=self.config.env,
        )
        try:
            yield self
        finally:
            await self.shutdown()


async def process_worker(
    process: LSPStdioProcess,
    client_resp_table: jsonrpc.ResponseTable,
    server_req_sender: Sender[ServerRequest],
) -> None:
    async def handle(package: jsonrpc.RawPackage):
        match package:
            case {"result": _, "id": id} | {"error": _, "id": id} as resp:
                await client_resp_table.send(id, resp)
            case {"id": id, "method": _} as req:
                tx, rx = jsonrpc.response_channel.create()
                await server_req_sender.send((req, tx))
                resp = await rx.receive()
                await process.send(resp)
            case {"method": _} as noti:
                await server_req_sender.send(noti)

    async with anyio.create_task_group() as tg:
        while package := await process.receive():
            tg.start_soon(handle, package)
