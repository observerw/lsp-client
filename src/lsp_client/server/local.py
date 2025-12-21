from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from functools import cached_property
from pathlib import Path
from typing import final, override

import anyio
from anyio.abc import AnyByteSendStream, Process
from anyio.streams.buffered import BufferedByteReceiveStream
from attrs import Factory, define, field
from loguru import logger

from lsp_client.jsonrpc.parse import read_raw_package, write_raw_package
from lsp_client.jsonrpc.types import RawPackage
from lsp_client.server.abc import LSPServer
from lsp_client.utils.workspace import Workspace


@final
@define
class LocalServer(LSPServer):
    command: Sequence[str]

    cwd: Path = Factory(Path.cwd)
    env: dict[str, str] | None = None
    shutdown_timeout: float = 5.0

    _process: Process = field(init=False)

    @cached_property
    def stdin(self) -> AnyByteSendStream:
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

    @override
    async def send(self, package: RawPackage) -> None:
        await write_raw_package(self.stdin, package)
        logger.debug("Package sent: {}", package)

    @override
    async def receive(self) -> RawPackage | None:
        try:
            package = await read_raw_package(self.stdout)
            logger.debug("Received package: {}", package)
            return package
        except (anyio.EndOfStream, anyio.IncompleteRead, anyio.ClosedResourceError):
            logger.debug("Process stdout closed")
            return None

    @override
    async def kill(self) -> None:
        logger.debug("Killing process")
        self._process.kill()
        await self._process.aclose()

    @override
    @asynccontextmanager
    async def run_process(self, workspace: Workspace) -> AsyncGenerator[None]:
        command = [*self.command, *self.args]
        logger.debug("Running with command: {}", command)

        try:
            self._process = await anyio.open_process(
                command, cwd=self.cwd, env=self.env
            )
            yield
        finally:
            try:
                with anyio.fail_after(self.shutdown_timeout):
                    if (returncode := await self._process.wait()) != 0:
                        logger.warning("Process exited with code {}", returncode)
                    else:
                        logger.debug("Process exited successfully")
            except TimeoutError:
                logger.warning("Process shutdown timeout reached, killing process")
                await self.kill()
