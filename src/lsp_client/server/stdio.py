from __future__ import annotations

import asyncio as aio
import os
import random
from abc import abstractmethod
from asyncio import StreamReader, StreamWriter
from collections.abc import AsyncGenerator, Generator, Sequence
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Self, override

from asyncio_addon import gather_all
from loguru import logger

from lsp_client import jsonrpc

from .base import LSPServerBase
from .jsonrpc import read_raw_package, write_raw_package


@dataclass(frozen=True)
class LSPServerInfo:
    cwd: Path = field(default=Path.cwd())
    env: dict[str, Any] | None = None


@dataclass(frozen=True)
class StdioProcess:
    type ID = str

    id: ID
    process: aio.subprocess.Process

    @classmethod
    async def create(
        cls,
        *cmd: str,
        id: str,
        info: LSPServerInfo,
    ) -> Self:
        process = await aio.create_subprocess_exec(
            *cmd,
            stdin=aio.subprocess.PIPE,
            stdout=aio.subprocess.PIPE,
            stderr=aio.subprocess.PIPE,
            cwd=info.cwd,
            env=info.env,
        )

        return cls(id=id, process=process)

    @property
    def stdin(self) -> StreamWriter:
        stdin = self.process.stdin
        assert stdin, "Process stdin is not available"
        return stdin

    @property
    def stdout(self) -> StreamReader:
        stdout = self.process.stdout
        assert stdout, "Process stdout is not available"
        return stdout

    @property
    def stderr(self) -> StreamReader:
        stderr = self.process.stderr
        assert stderr, "Process stderr is not available"
        return stderr

    async def receive_package(self) -> jsonrpc.RawPackage:
        package = await read_raw_package(self.stdout)
        logger.debug("Received package: {}", package)
        return package

    async def send_package(self, package: jsonrpc.RawPackage) -> None:
        await write_raw_package(self.stdin, package)
        logger.debug("Package sent: {}", package)

    async def shutdown(self) -> None:
        try:
            if returncode := await aio.wait_for(self.process.wait(), timeout=5.0):
                logger.debug(
                    "Process {} exited with code {}",
                    self.id,
                    returncode,
                )
        except TimeoutError:
            logger.warning(
                "Process %s shutdown timeout reached, killing process",
                self.id,
            )
            self.process.kill()
            _ = await self.process.wait()
            logger.debug(
                "Process %s killed after timeout",
                self.id,
            )


@dataclass
class StdioServerRuntime:
    resp_table: jsonrpc.ResponseTable
    processes: list[StdioProcess]
    tg: aio.TaskGroup

    # for server-side requests
    sender: jsonrpc.ReqSender
    receiver: jsonrpc.ReqReceiver


@dataclass
class StdioServer(LSPServerBase):
    _runtime: StdioServerRuntime | None = field(default=None, init=False)

    process_count: int | None = 1
    info: LSPServerInfo = field(default_factory=LSPServerInfo)
    buffer_size: int = 0

    @property
    @abstractmethod
    def server_cmd(self) -> Sequence[str]: ...

    @property
    def runtime(self) -> StdioServerRuntime:
        if not self._runtime:
            raise RuntimeError("LSPServerRuntime is not initialized")

        return self._runtime

    @contextmanager
    def next_server(self) -> Generator[StdioProcess]:
        yield random.choice(self.runtime.processes)

    @override
    async def request(self, request: jsonrpc.RawRequest) -> jsonrpc.RawResponsePackage:
        tx, rx = jsonrpc.response_channel.create()
        with self.next_server() as process:
            await process.send_package(request)
            await self.runtime.resp_table.register(request["id"], tx)
            return await rx.receive()

    @override
    async def request_all(
        self, requests: jsonrpc.RawRequest
    ) -> Sequence[jsonrpc.RawResponsePackage]:
        tx, rx = jsonrpc.many_response_channel.create(
            expect_count=len(self.runtime.processes)
        )
        await gather_all(
            process.send_package(requests)  #
            for process in self.runtime.processes
        )
        await self.runtime.resp_table.register(requests["id"], tx)
        return await rx.receive()

    @override
    async def notify(self, notification: jsonrpc.RawNotification) -> None:
        await gather_all(
            process.send_package(notification)  #
            for process in self.runtime.processes
        )

    @property
    @override
    def server_request_receiver(self) -> jsonrpc.ReqReceiver:
        return self.runtime.receiver

    @override
    @asynccontextmanager
    async def serve(self) -> AsyncGenerator[Self]:
        if self._runtime:
            yield self

        process_count = self.process_count or os.cpu_count() or 1
        assert process_count >= 1, f"Invalid process count: {process_count}"
        processes = await gather_all(
            StdioProcess.create(
                *self.server_cmd,
                id=f"process-{i}",
                info=self.info,
            )
            for i in range(process_count)
        )
        sender, receiver = jsonrpc.request_channel.create(buffer_size=self.buffer_size)

        try:
            async with aio.TaskGroup() as tg:
                self._runtime = StdioServerRuntime(
                    resp_table=jsonrpc.ResponseTable(),
                    tg=tg,
                    processes=[*processes],
                    sender=sender,
                    receiver=receiver,
                )
                logger.info(
                    "LSPServerPool initialized with {} processes", len(processes)
                )

                process_worker_tasks = [
                    tg.create_task(self._process_worker(process))
                    for process in self.runtime.processes
                ]

                yield self

                # if client yielded with no exception,
                # safely cancel all process worker tasks
                # or TaskGroup will help us cancel them
                for task in process_worker_tasks:
                    canceled = task.cancel()
                    assert canceled, "Process worker task is not canceled"

        finally:  # clean up runtime
            await self.runtime.sender.join()
            await self.runtime.resp_table.wait_complete()
            await gather_all(process.shutdown() for process in self.runtime.processes)

            self._runtime = None

    async def _process_worker(self, process: StdioProcess):
        """Worker to handle incoming packages from the LSP server's stdout. Must terminate by cancellation."""

        async def handle(package: jsonrpc.RawPackage):
            match package:
                case {"result": _, "id": id} | {"error": _, "id": id} as resp:
                    await self.runtime.resp_table.send(id, resp)
                case {"id": id, "method": _} as req:
                    tx, rx = jsonrpc.response_channel.create()
                    await self.runtime.sender.send((req, tx))
                    resp = await rx.receive()
                    await process.send_package(resp)
                case {"method": _} as noti:
                    await self.runtime.sender.send(noti)

        async with aio.TaskGroup() as tg:
            while True:
                package = await process.receive_package()
                tg.create_task(handle(package))
