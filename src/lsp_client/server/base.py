from __future__ import annotations

from abc import abstractmethod
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from typing import Literal, Self, override

import anyio
from attrs import Factory, define, field, frozen

from lsp_client import jsonrpc
from lsp_client.utils.channel import Sender

from .process import LSPStdioProcess, ProcessConfig, process_worker
from .type import ServerRequest


@frozen
class LSPServerConfig(ProcessConfig): ...


type LSPServerRuntime = Literal["local", "docker", "podman"]


@define(kw_only=True)
class LSPServer:
    config: LSPServerConfig = Factory(LSPServerConfig)
    runtime: LSPServerRuntime = "local"
    container_image: str | None = None

    resp_table: jsonrpc.ResponseTable = field(init=False)
    process: LSPStdioProcess = field(init=False)

    @property
    @abstractmethod
    def server_cmd(self) -> Sequence[str]: ...

    @property
    def container_cmd(self) -> Sequence[str]:
        assert self.container_image

        return (
            self.runtime,
            "run",
            "--rm",
            "-i",
            self.container_image,
        )

    @property
    def server_args(self) -> Sequence[str]:
        return ()

    @property
    def process_cmd(self) -> Sequence[str]:
        match self.runtime:
            case "local":
                cmd = self.server_cmd
            case "docker" | "podman" | "runc":
                if not self.container_image:
                    raise ValueError(
                        f"There is no container image right now for {self.runtime}"
                    )

                cmd = self.container_cmd

        return (
            *cmd,
            *self.server_args,
        )

    @override
    @asynccontextmanager
    async def _start(self, sender: Sender[ServerRequest]) -> AsyncGenerator[Self]:
        """
        Start serving the LSP server.

        This method is not a public API. It is intended to be called only by `LSPClient`.
        """

        async with (
            anyio.create_task_group() as worker_tg,
            LSPStdioProcess(cmd=self.process_cmd, config=self.config) as process,
        ):
            self.resp_table = jsonrpc.ResponseTable()
            self.process = process

            worker_tg.start_soon(process_worker, self.process, self.resp_table, sender)

            yield self

    async def _request(self, request: jsonrpc.RawRequest) -> jsonrpc.RawResponsePackage:
        await self.process.send(request)
        return await self.resp_table.receive(request["id"])

    async def _notify(self, notification: jsonrpc.RawNotification) -> None:
        await self.process.send(notification)
