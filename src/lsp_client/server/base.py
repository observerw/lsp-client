from __future__ import annotations

import asyncio as aio
import logging
import random
from collections.abc import Generator, Sequence
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from typing import Any

from asyncio_addon import gather_all

from lsp_client.jsonrpc import (
    JsonRpcRawNotification,
    JsonRpcRawPackage,
    JsonRpcRawRequest,
    JsonRpcRawRespPackage,
)

from .event import BatchRequestEvent, RequestManager, SingleRequestEvent
from .process import LSPServerInfo, LSPServerProcess
from .types import ServerRequestQueue

logger = logging.getLogger(__name__)


@dataclass
class LSPServerPool:
    processes: Sequence[LSPServerProcess]
    server_req_queue: ServerRequestQueue
    manager: RequestManager

    _closed: bool = False

    def _check_closed(self):
        if self._closed:
            raise RuntimeError(
                "LSP server pool is closed, cannot perform any operations."
            )

    async def _handle_package(
        self, process: LSPServerProcess, package: JsonRpcRawPackage
    ) -> None:
        match package:
            case {"result": _} | {"error": _} as resp:
                await self.manager.respond(resp)
            case {"id": id, "method": method} as req:
                assert id, f"Invalid server request package: {package}"
                async with self.manager.request(
                    SingleRequestEvent(id=id, method=method)
                ) as event:
                    await self.server_req_queue.put(req)
                await process.send_package(event.get_data())
            case {"method": _} as noti:
                await self.server_req_queue.put(noti)

    async def _server_worker(self, process: LSPServerProcess):
        """Worker to handle incoming packages from the LSP server's stdout. Must terminate by cancellation."""

        async with aio.TaskGroup() as tg:
            while True:
                package = await process.receive_package()
                tg.create_task(self._handle_package(process, package))
        # all received packages are handled

    @classmethod
    @asynccontextmanager
    async def load(
        cls,
        server_cmd: Sequence[str],
        server_req_queue: ServerRequestQueue,
        *,
        process_count: int = 1,
        info: LSPServerInfo | None = None,
        pending_timeout: float | None = None,
    ):
        processes = await gather_all(
            LSPServerProcess.create(
                *server_cmd,
                id=f"process-{i}",
                info=info or LSPServerInfo(),
            )
            for i in range(process_count)
        )
        logger.info("LSPServerPool initialized with %d processes", len(processes))

        server_pool = cls(
            processes=processes,
            server_req_queue=server_req_queue,
            manager=RequestManager(timeout=pending_timeout),
        )

        yield server_pool

        await gather_all(process.shutdown() for process in processes)
        logger.info("all LSP server processes are shut down gracefully")
        server_pool._closed = True
        # all server processes are shut down

    @asynccontextmanager
    async def start(self):
        """Start service workers, wait until all pending requests are completed, and client requests to shutdown."""

        async with aio.TaskGroup() as tg:
            tasks = [
                tg.create_task(self._server_worker(process))
                for process in self.processes
            ]

            yield
            # all client side requests are registered, and client requests to shutdown

            await self.manager.wait_complete()
            # all client side requests are responded

            for task in tasks:
                assert task.cancel()
            # safely cancel all server side request workers

    @contextmanager
    def next_server(self) -> Generator[LSPServerProcess, Any]:
        # TODO more sophisticated load balancing

        yield random.choice(self.processes)

    async def request(self, req: JsonRpcRawRequest) -> JsonRpcRawRespPackage:
        self._check_closed()

        with self.next_server() as process:
            assert req["id"], "LSPRequest must have an id"

            async with self.manager.request(
                SingleRequestEvent(id=req["id"], method=req["method"])
            ) as event:
                await process.send_package(req)
        return event.get_data()

    async def request_all(
        self, req: JsonRpcRawRequest
    ) -> Sequence[JsonRpcRawRespPackage]:
        self._check_closed()

        assert req["id"], "LSPRequest must have an id"
        async with self.manager.request(
            BatchRequestEvent(
                id=req["id"],
                method=req["method"],
                expected_count=len(self.processes),
            )
        ) as event:
            await gather_all(process.send_package(req) for process in self.processes)
        return event.get_data()

    async def respond(self, resp: JsonRpcRawRespPackage):
        """Respond to a server-side request."""
        self._check_closed()

        await self.manager.respond(resp)

    async def notify_all(self, req: JsonRpcRawNotification):
        """Notify all server processes."""
        self._check_closed()

        await gather_all(process.send_package(req) for process in self.processes)
