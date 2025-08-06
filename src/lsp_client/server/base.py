from __future__ import annotations

import asyncio as aio
import os
import random
from abc import abstractmethod
from collections.abc import AsyncGenerator, Generator, Sequence
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from typing import Any, Self

from asyncio_addon import gather_all
from loguru import logger

from lsp_client import jsonrpc
from lsp_client.channel import ManyShotSender, OneShotSender

from .process import LSPServerInfo, LSPServerProcess


@dataclass(frozen=True)
class ServerRuntimeArgs:
    sender: jsonrpc.RequestSender
    receiver: jsonrpc.RequestReceiver


@dataclass(frozen=True)
class ServerArgs:
    server_count: int | None = 1
    """The number of LSP server processes to start. If None, defaults to the number of CPU cores."""

    server_info: LSPServerInfo = field(default_factory=LSPServerInfo)
    """Runtime information for the LSP server."""

    @property
    @abstractmethod
    def server_cmd(self) -> Sequence[str]:
        """The command to start the LSP server."""


@dataclass
class LSPServerPool:
    _runtime: ServerRuntimeArgs
    _args: ServerArgs

    _client_req_table: jsonrpc.ResponseTable

    _processes: Sequence[LSPServerProcess]
    _closed: bool = False

    @property
    def process_count(self) -> int:
        return len(self._processes)

    def _check_closed(self):
        if self._closed:
            raise RuntimeError(
                "LSP server pool is closed, cannot perform any operations."
            )

    async def _process_worker(self, process: LSPServerProcess):
        """Worker to handle incoming packages from the LSP server's stdout. Must terminate by cancellation."""

        async def handle(package: jsonrpc.RawPackage):
            match package:
                case {"result": _, "id": id} | {"error": _, "id": id} as resp:
                    await self._client_req_table.send(id, resp)
                case {"id": id, "method": _} as req:
                    tx, rx = jsonrpc.response_channel.create()
                    await self._runtime.sender.send((req, tx))
                    resp = await rx.receive()
                    await process.send_package(resp)
                case {"method": _} as noti:
                    await self._runtime.sender.send(noti)

        async with aio.TaskGroup() as tg:
            while True:
                package = await process.receive_package()
                tg.create_task(handle(package))

    async def _client_worker(self):
        async def send_req(
            process: LSPServerProcess,
            req: jsonrpc.RawRequest,
            sender: jsonrpc.RespSender | jsonrpc.ManyRespSender,
        ):
            match req:
                case {"id": id}:
                    assert id is not None, "LSPRequest must have an id"
                    await process.send_package(req)
                    # register the request in the client request table,
                    # wait for the process to respond
                    await self._client_req_table.register(id, sender)
                case _:
                    raise ValueError(f"Invalid request payload: {req}")

        async def handle(req: jsonrpc.ChannelRequest):
            match req:
                case (req, OneShotSender() as sender):
                    with self.next_server() as process:
                        await send_req(process, req, sender)
                case (req, ManyShotSender() as sender):
                    # send request to all server processes
                    await gather_all(
                        send_req(process, req, sender) for process in self._processes
                    )
                case noti:
                    await gather_all(
                        process.send_package(noti) for process in self._processes
                    )

            # don't forget!
            self._runtime.receiver.task_done()

        async with aio.TaskGroup() as tg:
            while True:
                req = await self._runtime.receiver.receive()
                tg.create_task(handle(req))

    @classmethod
    @asynccontextmanager
    async def start(
        cls,
        args: ServerArgs,
        runtime_args: ServerRuntimeArgs,
    ) -> AsyncGenerator[Self]:
        process_count = args.server_count or os.cpu_count() or 1
        assert process_count >= 1, f"Invalid process count: {process_count}"

        processes = await gather_all(
            LSPServerProcess.create(
                *args.server_cmd,
                id=f"process-{i}",
                info=args.server_info,
            )
            for i in range(process_count)
        )

        instance = cls(
            _runtime=runtime_args,
            _args=args,
            _client_req_table=jsonrpc.ResponseTable(),
            _processes=processes,
        )

        logger.info("LSPServerPool initialized with {} processes", len(processes))

        async with aio.TaskGroup() as tg:
            process_tasks = [
                tg.create_task(instance._process_worker(process))
                for process in processes
            ]
            client_task = tg.create_task(instance._client_worker())

            logger.info("LSPServerPool started")

            yield instance
            # all client side requests are registered, and client requests to shutdown

            await instance._client_req_table.wait_complete()
            # all client side requests are responded
            logger.info("all client side requests are completed")

            await instance._runtime.receiver.join()

            for task in process_tasks:
                assert task.cancel()
            assert client_task.cancel()

            logger.info("all server side request workers are finished")

        await gather_all(process.shutdown() for process in processes)
        logger.info("all LSP server processes are shut down gracefully")
        instance._closed = True
        # all server processes are shut down

    @contextmanager
    def next_server(self) -> Generator[LSPServerProcess, Any]:
        # TODO more sophisticated load balancing

        yield random.choice(self._processes)
