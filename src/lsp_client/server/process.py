from __future__ import annotations

import asyncio as aio
from asyncio import StreamReader, StreamWriter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Self

from loguru import logger

from lsp_client import jsonrpc

from .jsonrpc import read_raw_package, write_raw_package


@dataclass(frozen=True)
class LSPServerInfo:
    cwd: Path = field(default=Path.cwd())
    env: dict[str, Any] | None = None


@dataclass(frozen=True)
class LSPServerProcess:
    type ID = str

    id: ID
    process: aio.subprocess.Process

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
