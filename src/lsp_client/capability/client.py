from __future__ import annotations

import asyncio as aio
import logging
import os
from abc import abstractmethod
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import cached_property
from itertools import product
from typing import Any, Protocol, Self, override

from asyncio_addon import gather_all
from lsprotocol import types

from lsp_client.jsonrpc import JsonRpcResponse, lsp_converter, response_deserialize
from lsp_client.server import LSPServerPool, ServerRequestQueue
from lsp_client.types import AnyPath
from lsp_client.utils.attrs import attrs_merges
from lsp_client.utils.path import AbsPath

from .file_buffer import LSPFileBuffer
from .notification import WithNotifyTextDocumentSynchronize
from .protocol import LSPCapabilityClientProtocol, LSPCapabilityProtocol
from .server_req import ServerRequestClient


@dataclass
class LSPCapabilityClientBase(
    # Client support for `textDocument/didOpen`, `textDocument/didChange` and `textDocument/didClose`
    # notifications is mandatory
    WithNotifyTextDocumentSynchronize,
    ServerRequestClient,
    LSPCapabilityClientProtocol,
    Protocol,
):
    _server: LSPServerPool
    _request_tg: aio.TaskGroup
    """Tasks of sending requests to the server and receiving responses."""

    _repo_path: AbsPath
    _logger: logging.Logger
    _closed: bool = False

    @property
    @override
    def repo_path(self) -> AbsPath:
        return self._repo_path

    @property
    @override
    def logger(self) -> logging.Logger:
        return self._logger

    @classmethod
    def client_capabilities(cls) -> types.ClientCapabilities:
        """
        All client capabilities for this LSP client.

        The final client capabilities are merged from all capabilities defined in the class hierarchy.
        """

        caps = [
            cap_cls.client_capability()
            for cap_cls in cls.mro()
            if issubclass(cap_cls, LSPCapabilityProtocol)  #
            and cap_cls is not LSPCapabilityClientProtocol
            and cap_cls is not cls
        ]

        merged = attrs_merges(*caps)
        assert isinstance(merged, types.ClientCapabilities)
        return merged

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
        repo_path: AbsPath,
        server: LSPServerPool,
        *,
        file_paths: Sequence[AnyPath] = (),
        initialization_options: dict[str, Any] | None = None,
    ) -> AsyncGenerator[Self, Any]:
        server_req_queue = ServerRequestQueue()
        logger = logging.getLogger(cls.__name__)

        async with server.start(), aio.TaskGroup() as tg:
            client = cls(
                server_req_queue=server_req_queue,
                _server=server,
                _repo_path=AbsPath(repo_path),
                _request_tg=tg,
                _logger=logger,
            )

            # initialize repo
            _ = await client.initialize(initialization_options=initialization_options)
            logger.info("LSP client initialized successfully.")

            # prepare for server side requests
            server_req_worker_task = tg.create_task(client._server_req_worker())

            try:
                yield client
                # all client side requests are sent
            finally:
                try:
                    pass
                    # _ = await client.shutdown()
                except TimeoutError as e:
                    raise TimeoutError(
                        "LSP client shutdown timed out, server failed to exit gracefully."
                    ) from e
                # request server to shutdown (but not exit)

                await client.server_req_queue.join()
                assert server_req_worker_task.cancel()
                # all server side requests are handled
            # all client side requests are sent
        # all client side requests are responded
        await client.exit()  # request server to exit
        client._closed = True

    # all server processes are exited

    @cached_property
    def file_buffer(self) -> LSPFileBuffer:
        return LSPFileBuffer()

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
            AbsPath(file_path, base_path=self._repo_path) for file_path in file_paths
        ]

        if not abs_file_paths:
            yield
            return

        try:
            buffer_items = self.file_buffer.open(abs_file_paths)
            await gather_all(
                self.notify_text_document_opened(
                    file_path=item.file_path,
                    file_content=item.content,
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
            raw_resp = await self._server.request(lsp_converter.unstructure(req))
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
            raw_resps = await self._server.request_all(lsp_converter.unstructure(req))
            return [response_deserialize(raw_resp, schema) for raw_resp in raw_resps]

    async def notify_all(self, msg: Any) -> None:
        self._check_closed()

        return await self._server.notify_all(lsp_converter.unstructure(msg))

    async def respond(self, resp: Any) -> None:
        self._check_closed()

        return await self._server.respond(lsp_converter.unstructure(resp))

    def create_request[T](self, coro: aio._CoroutineLike[T]) -> aio.Task[T]:
        self._check_closed()

        return self._request_tg.create_task(coro)

    async def initialize(self, initialization_options: dict[str, Any] | None = None):
        """Initialize parameters for the LSP client."""

        root_uri = self._repo_path.as_uri()
        root_path_posix = self._repo_path.as_posix()

        initialize_params = types.InitializeParams(
            capabilities=self.client_capabilities(),
            process_id=os.getpid(),
            client_info=types.ClientInfo(
                name="LSP Client",
                version="1.81.0-insider",
            ),
            locale="en-us",
            root_path=root_path_posix,
            root_uri=root_uri,
            initialization_options=initialization_options,
            trace=types.TraceValue.Verbose,
            workspace_folders=[
                types.WorkspaceFolder(
                    uri=root_uri,
                    name=self._repo_path.name,
                )
            ],
        )

        results = await self.request_all(
            types.InitializeRequest(
                id="intialize",
                params=initialize_params,
            ),
            schema=types.InitializeResponse,
        )

        # check for server capabilities
        cls = self.__class__
        for result, cap_cls in product(results, cls.mro()):
            if not (
                issubclass(cap_cls, LSPCapabilityProtocol)
                and cap_cls is not LSPCapabilityClientProtocol
                and cap_cls is not cls
            ):
                continue

            cap_cls.check_server_capability(
                result.capabilities,
                result.server_info,
            )

        await self.notify_all(
            types.InitializedNotification(
                params=types.InitializedParams(),
            )
        )

    async def shutdown(self):
        """
        `shutdown` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#shutdown
        """

        await self.request_all(
            types.ShutdownRequest(
                id="shutdown",
            ),
            schema=types.ShutdownResponse,
        )

    async def exit(self) -> None:
        """
        `exit` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#exit
        """

        await self.notify_all(types.ExitNotification())

    @abstractmethod
    def check_server_compatibility(self, info: types.ServerInfo | None):
        """Check if the available server capabilities are compatible with the client."""
