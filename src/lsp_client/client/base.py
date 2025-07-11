from __future__ import annotations

import asyncio as aio
import inspect
import logging
from collections.abc import Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import cached_property
from typing import Any, ClassVar, Protocol, override

from asyncio_addon import gather_all

import lsp_client.capability as cap
from lsp_client.jsonrpc import JsonRpcResponse, lsp_converter, response_deserialize
from lsp_client.server import LSPServerInfo, LSPServerPool, ServerRequestQueue
from lsp_client.types import AnyPath
from lsp_client.utils.path import AbsPath

from .buffer import LSPFileBuffer
from .server_req import ServerRequestClient


@dataclass
class LSPClientBase(
    # Client support for textDocument/didOpen, textDocument/didChange and textDocument/didClose notifications is mandatory
    cap.WithNotifyTextDocumentSynchronize,
    ServerRequestClient,
    cap.LSPCapabilityClient,
    Protocol,
):
    server_cmd: ClassVar[Sequence[str]]

    server: LSPServerPool
    repo_path: AbsPath

    request_tg: aio.TaskGroup
    """Tasks of sending requests to the server and receiving responses."""

    logger: logging.Logger
    _closed: bool = False

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if inspect.isabstract(cls):
            return

        cls.check_client_capability()
        cls.check_version_capability()

    def auto_install(self, base_path: AnyPath | None = None) -> None:
        """
        Automatically install the LSP server.

        Args:
            base_path (AnyPath | None): The base path to install the server. If None, the server will be installed in the current working directory.
        """

        raise NotImplementedError(
            f"{self.__class__.__name__} does not provide auto-installation of LSP server. Please install the server manually."
        )

    @classmethod
    @asynccontextmanager
    async def start(
        cls,
        repo_path: AnyPath,
        *,
        server_count: int = 1,
        server_info: LSPServerInfo | None = None,
        file_paths: Sequence[AnyPath] = (),
        pending_timeout: float | None = 5.0,
    ):
        """
        Start the LSP client.

        To perform LSP operations, you need to use this method with `async with` clause. After exit the context, the client will be closed and no further operations can be performed.

        Args:
            repo_path (AnyPath): The path to the repository.
            server_count (int, optional): The maximum number of LSP server processes to start. Defaults to 1.
            server_info (LSPServerInfo, optional): Information about the LSP server. Defaults to LSPServerInfo().
            file_paths (Sequence[AnyPath], optional): Pre-opened file paths available for the client. Defaults to ().
            pending_timeout (float | None, optional): Timeout since a request is sent to the server until it is responded. If None, no timeout is applied. Defaults to 5 seconds.

        Yields:
            LSPClientBase: An instance of the LSP client that is ready to use.
        """

        server_req_queue = ServerRequestQueue()
        logger = logging.getLogger(cls.__name__)
        async with (
            LSPServerPool.load(
                server_cmd=cls.server_cmd,
                server_req_queue=server_req_queue,
                process_count=server_count,
                info=server_info or LSPServerInfo(),
                pending_timeout=pending_timeout,
            ) as server,
        ):
            async with server.start(), aio.TaskGroup() as tg:
                client = cls(
                    server=server,
                    repo_path=AbsPath(repo_path),
                    request_tg=tg,
                    server_req_queue=server_req_queue,
                    logger=logger,
                )

                # initialize repo
                _ = await client.initialize()

                # prepare for server side requests
                server_req_worker_task = tg.create_task(client._server_req_worker())

                try:
                    async with client.open_files(*file_paths):
                        yield client
                    # all client side requests are sent
                finally:
                    try:
                        _ = await client.shutdown()
                    except TimeoutError as e:
                        raise TimeoutError(
                            "LSP client shutdown timed out, server failed to exit gracefully."
                        ) from e

                    # request server to shutdown (but not exit)

                    await client.server_req_queue.join()
                    assert server_req_worker_task.cancel()
                    # Signal the worker to exit
                # all server side requests are handled
            # all client side requests are sent
            # all client side requests are responded
            await client.exit()  # request server to exit
            client._closed = True
        # all server processes are exited

    @cached_property
    def file_buffer(self) -> LSPFileBuffer:
        return LSPFileBuffer(language_id=self.language_id)

    def _check_closed(self):
        if self._closed:
            raise RuntimeError("LSP client is closed, cannot perform any operations.")

    @property
    def closed(self) -> bool:
        """
        Check if the LSP client is closed. If closed, no further LSP operations can be performed.
        """

        return self._closed

    @asynccontextmanager
    async def open_files(self, *file_paths: AnyPath):
        """
        Open files in the LSP client.

        This is required to be call before performing any requests that will modify the file content.

        Usually, file-change operations will automatically open the files, perform the operations, and close the files.

        If you know for sure that a set of files will be used in the following requests, you can pre-open them using this method. This will help to reduce the overhead of opening and closing files repeatedly.

        Args:
            file_paths(Sequence[AnyPath]): The file paths to open.
        """

        self._check_closed()

        abs_file_paths = [
            AbsPath(file_path, base_path=self.repo_path) for file_path in file_paths
        ]

        if not abs_file_paths:
            yield
            return

        try:
            buffer_items = self.file_buffer.open(abs_file_paths)
            await gather_all(
                self.notify_text_document_opened(
                    file_path=item.file_path,
                    file_content=item.contents,
                )
                for item in buffer_items
            )
            yield
        finally:
            closed_files = self.file_buffer.close(abs_file_paths)
            await gather_all(
                self.notify_text_document_closed(file_path=path)
                for path in closed_files
            )

    @override
    async def request[R](
        self,
        req: Any,
        schema: type[JsonRpcResponse[R]],
        *,
        file_paths: Sequence[AnyPath] = (),
    ) -> R:
        """
        Note that the `params` are required to be a `attr` model defined in `lsprotocol.types`.
        """

        self._check_closed()

        async with self.open_files(*file_paths):
            raw_resp = await self.server.request(lsp_converter.unstructure(req))
            return response_deserialize(raw_resp, schema)

    async def request_all[R](
        self,
        req: Any,
        schema: type[JsonRpcResponse[R]],
        *,
        file_paths: Sequence[AnyPath] = (),
    ) -> Sequence[R]:
        """
        Similar to `request`, but sends the request to all servers in the pool.
        This is useful for operations that need to be performed across all servers.
        """

        self._check_closed()

        async with self.open_files(*file_paths):
            raw_resps = await self.server.request_all(lsp_converter.unstructure(req))
            return [response_deserialize(raw_resp, schema) for raw_resp in raw_resps]

    async def notify_all(self, msg: Any) -> None:
        self._check_closed()

        return await self.server.notify_all(lsp_converter.unstructure(msg))

    async def respond(self, resp: Any) -> None:
        self._check_closed()

        return await self.server.respond(lsp_converter.unstructure(resp))

    def create_request[T](self, coro: aio._CoroutineLike[T]) -> aio.Task[T]:
        self._check_closed()

        return self.request_tg.create_task(coro)
