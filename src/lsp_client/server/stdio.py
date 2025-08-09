from __future__ import annotations

import asyncio as aio
import os
import random
from abc import abstractmethod
from asyncio import StreamReader, StreamWriter
from collections.abc import AsyncGenerator, Generator, Sequence
from contextlib import AsyncExitStack, asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Self, override

from asyncio_addon import gather_all
from loguru import logger

from lsp_client import jsonrpc
from lsp_client.types import Workspace

from .base import LSPServerBase, ServerRequest
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

    async def send(self, package: jsonrpc.RawPackage) -> None:
        await write_raw_package(self.stdin, package)
        logger.debug("Package sent: {}", package)

    async def receive(self) -> jsonrpc.RawPackage | None:
        try:
            package = await read_raw_package(self.stdout)
            logger.debug("Received package: {}", package)
            return package
        except EOFError:
            logger.debug("Process {} stdout closed", self.id)
            return None

    async def shutdown(self) -> int:
        try:
            returncode = await aio.wait_for(self.process.wait(), timeout=5.0)
            logger.debug("Process {} exited with code {}", self.id, returncode)
            return returncode
        except TimeoutError:
            logger.warning(
                "Process {} shutdown timeout reached, killing process",
                self.id,
            )
            self.process.kill()
            return 1

    @classmethod
    @asynccontextmanager
    async def serve(
        cls, *cmd: str, id: str, info: LSPServerInfo
    ) -> AsyncGenerator[StdioProcess]:
        process = await cls.create(*cmd, id=id, info=info)
        try:
            yield process
        finally:
            await process.shutdown()


@dataclass
class StdioServerRuntime:
    processes: list[StdioProcess]
    resp_table: jsonrpc.ResponseTable

    # server-side requests
    queue: aio.Queue[ServerRequest]

    # only after server start to `serve` will the `workspace` be set here
    workspace: Workspace | None = None


@dataclass
class StdioServer(LSPServerBase):
    _runtime: StdioServerRuntime | None = field(default=None, init=False)

    process_count: int | None
    info: LSPServerInfo

    buffer_size: int = 0

    @property
    @abstractmethod
    def server_cmd(self) -> Sequence[str]: ...

    @property
    def runtime(self) -> StdioServerRuntime:
        if not self._runtime:
            raise RuntimeError("Server is not running")

        return self._runtime

    @property
    def workspace(self) -> Workspace:
        if not self.runtime.workspace:
            raise RuntimeError("Server is not initialized")

        return self.runtime.workspace

    @contextmanager
    def next_server(self) -> Generator[StdioProcess]:
        # TODO implement more sophisticated load-balancing strategy
        yield random.choice(self.runtime.processes)

    @override
    async def request(self, request: jsonrpc.RawRequest) -> jsonrpc.RawResponsePackage:
        with self.next_server() as process:
            await process.send(request)
            return await self.runtime.resp_table.wait(request["id"])

    @override
    async def request_all(
        self, request: jsonrpc.RawRequest
    ) -> Sequence[jsonrpc.RawResponsePackage]:
        await gather_all(
            process.send(request)  #
            for process in self.runtime.processes
        )
        return await self.runtime.resp_table.wait_many(
            request["id"], expect_count=len(self.runtime.processes)
        )

    @override
    async def notify(self, notification: jsonrpc.RawNotification) -> None:
        await gather_all(
            process.send(notification)  #
            for process in self.runtime.processes
        )

    @property
    @override
    def server_request_queue(self) -> aio.Queue[ServerRequest]:
        return self.runtime.queue

    @override
    @asynccontextmanager
    async def run(self) -> AsyncGenerator[Self]:
        if self._runtime:
            yield self

        process_count = self.process_count or os.cpu_count() or 1
        assert process_count >= 1, f"Invalid process count: {process_count}"

        async with (
            aio.TaskGroup() as worker_tg,
            AsyncExitStack() as process_stack,
        ):
            processes = await gather_all(
                process_stack.enter_async_context(
                    StdioProcess.serve(
                        *self.server_cmd,
                        id=f"process-{i}",
                        info=self.info,
                    )
                )
                for i in range(process_count)
            )

            self._runtime = StdioServerRuntime(
                resp_table=jsonrpc.ResponseTable(),
                processes=[*processes],
                queue=aio.Queue(),
            )

            for process in self.runtime.processes:
                worker_tg.create_task(self._process_worker(process))

            logger.debug("LSPServerPool initialized with {} processes", len(processes))

            yield self

        # LSP spec not specify when should server stop sending server-side requests,
        # so we shutdown the queue after processes exit for safety
        self.runtime.queue.shutdown()

        self._runtime = None
        logger.debug("LSPServerPool exit")

    @override
    @asynccontextmanager
    async def serve(self, workspace: Workspace) -> AsyncGenerator[Self]:
        if not self._runtime:
            raise RuntimeError("Server is not running")

        if self.runtime.workspace:
            raise RuntimeError("Server can only be initialized once")

        self.runtime.workspace = workspace

        try:
            yield self
        finally:  # clean up runtime
            # respond to `shutdown` indicates that servers have already
            # responded to all client-side requests, therefore the resp_table
            # is supposed to be completed here
            assert self.runtime.resp_table.completed
            logger.debug("LSPServerPool shutdown")

    async def _process_worker(self, process: StdioProcess):
        async def handle(package: jsonrpc.RawPackage):
            match package:
                case {"result": _, "id": id} | {"error": _, "id": id} as resp:
                    await self.runtime.resp_table.send(id, resp)
                case {"id": id, "method": _} as req:
                    tx, rx = jsonrpc.response_channel.create()
                    await self.runtime.queue.put((req, tx))
                    resp = await rx.receive()
                    await process.send(resp)
                case {"method": _} as noti:
                    await self.runtime.queue.put(noti)

        async with aio.TaskGroup() as tg:
            while package := await process.receive():
                tg.create_task(handle(package))


@dataclass
class DockerStdioServer(StdioServer):
    @property
    @abstractmethod
    def docker_args(self) -> Sequence[str]: ...

    @property
    @override
    def server_cmd(self) -> Sequence[str]:
        return (
            "docker",
            "run",
            "--rm",
            "-i",
            *self.docker_args,
        )
