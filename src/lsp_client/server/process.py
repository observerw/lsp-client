from __future__ import annotations

import asyncio as aio
import logging
from asyncio import StreamReader, StreamWriter
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any, Self

from lsp_client.jsonrpc import JsonRpcRawPackage

from .jsonrpc import read_raw_package, write_raw_package

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LSPServerInfo:
    cwd: Path = field(default=Path.cwd())
    env: dict[str, Any] | None = None


@dataclass(frozen=True)
class LSPServerProcess:
    type ID = str

    id: ID
    process: aio.subprocess.Process

    @cached_property
    def logger(self) -> logging.Logger:
        return logging.getLogger(f"{__name__} LSP Server [{self.id}]")

    @classmethod
    async def create(cls, *cmd: str, id: str, info: LSPServerInfo) -> Self:
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
        assert (stdin := self.process.stdin)
        return stdin

    @property
    def stdout(self) -> StreamReader:
        assert (stdout := self.process.stdout)
        return stdout

    @property
    def stderr(self) -> StreamReader:
        assert (stderr := self.process.stderr)
        return stderr

    async def receive_package(self) -> JsonRpcRawPackage:
        package = await read_raw_package(self.stdout)
        self.logger.debug("Received package: %s", package)
        return package

    async def send_package(self, package: JsonRpcRawPackage) -> None:
        await write_raw_package(self.stdin, package)
        self.logger.debug("Package sent: %s", package)

    async def shutdown(self) -> None:
        try:
            if returncode := await aio.wait_for(self.process.wait(), timeout=5.0):
                self.logger.debug(
                    "Process %s exited with code %d",
                    self.id,
                    returncode,
                )
        except TimeoutError:
            self.logger.warning(
                "Process %s shutdown timeout reached, killing process",
                self.id,
            )
            self.process.kill()
            await self.process.wait()
            self.logger.debug(
                "Process %s killed after timeout",
                self.id,
            )
