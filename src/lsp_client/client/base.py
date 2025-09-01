from __future__ import annotations

import os
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from functools import cached_property, partial
from pathlib import Path
from typing import Any, Self, override

import aiometer
import anyio
import attrs
from anyio import AsyncContextManagerMixin
from attrs import define, field
from loguru import logger
from lsprotocol import types

from lsp_client import jsonrpc
from lsp_client.capability.file_buffer import LSPFileBuffer
from lsp_client.capability.notification import WithNotifyTextDocumentSynchronize
from lsp_client.capability.protocol import (
    LSPCapabilityClientProtocol,
    LSPCapabilityProtocol,
)
from lsp_client.server import LSPServer
from lsp_client.server.type import ServerRequest
from lsp_client.types import AnyPath, Notification, Workspace, WorkspaceFolder
from lsp_client.utils.attrs import attrs_merges
from lsp_client.utils.channel import channel
from lsp_client.utils.path import AbsPath, from_local_uri

from .server_req import ServerRequestMixin
from .utils import ROOT_FOLDER_NAME, format_workspace


@define
class LSPClient[Server: LSPServer](
    # Client support for `textDocument/didOpen`, `textDocument/didChange` and `textDocument/didClose`
    # notifications is mandatory
    WithNotifyTextDocumentSynchronize,
    LSPCapabilityClientProtocol,
    AsyncContextManagerMixin,
    ServerRequestMixin,
    ABC,
):
    server: Server
    """LSP server this client is connected to."""

    workspace: Workspace = field(converter=format_workspace)
    """
    Workspace path(s) for the client to run on.

    Can be a single path (single-root workspace), or multiple path with unique identifier (multiple-root worksapce).
    """

    sync_file: bool = True
    """Whether to synchronize file (open, close, changed, etc.) when performing file-related operations."""

    pending_timeout: float | None = 10.0
    """Timeout for pending requests."""

    @abstractmethod
    def create_initialization_options(self) -> dict[str, Any] | None: ...

    @abstractmethod
    def check_server_compatibility(self, info: types.ServerInfo | None):
        """Check if the available server capabilities are compatible with the client."""

    @property
    @override
    def workspace_folders(self) -> Sequence[WorkspaceFolder]:
        return [*self.workspace.values()]

    @classmethod
    def client_capabilities(cls) -> types.ClientCapabilities:
        """
        All client capabilities for this LSP client.

        The final client capabilities are merged from all capabilities defined in the class hierarchy.
        """

        # reverse mro order so derived capabilities takes precedence
        reversed_mro = reversed(cls.mro())
        caps = [
            cap_cls.client_capability()
            for cap_cls in reversed_mro
            if issubclass(cap_cls, LSPCapabilityProtocol)  #
            and cap_cls is not LSPCapabilityClientProtocol
            and cap_cls is not cls
        ]

        merged = attrs_merges(*caps)
        assert isinstance(merged, types.ClientCapabilities)
        return merged

    @override
    @asynccontextmanager
    async def __asynccontextmanager__(self) -> AsyncGenerator[Self]:
        sender, receiver = channel[ServerRequest].create()

        async with (
            anyio.create_task_group() as worker_tg,
            self.server._start(sender=sender),
        ):
            # server notification can be sent before initialize
            worker_tg.start_soon(self._server_request_worker, receiver)

            # if single workspace root provided, set `root_path` and `root_uri` for compatibility
            root_workspace = self.workspace.get(ROOT_FOLDER_NAME)
            root_path = root_workspace.path.as_posix() if root_workspace else None
            root_uri = root_workspace.uri if root_workspace else None

            _ = await self._initialize(
                types.InitializeParams(
                    capabilities=self.client_capabilities(),
                    process_id=os.getpid(),
                    client_info=types.ClientInfo(
                        name="LSP Client",
                        version="1.81.0-insider",
                    ),
                    locale="en-us",
                    initialization_options=self.create_initialization_options(),
                    trace=types.TraceValue.Verbose,
                    root_path=root_path,
                    root_uri=root_uri,
                    workspace_folders=self.workspace_folders,
                )
            )

            try:
                yield self
            finally:
                _ = await self._shutdown()
                await self._exit()

    @cached_property
    def file_buffer(self) -> LSPFileBuffer:
        return LSPFileBuffer()

    @override
    def as_uri(self, file_path: AnyPath) -> str:
        """
        Turn a file path into a URI.

        For multi-root workspace, using the first part of a relative path as the workspace folder name.
        """

        if (file_path := Path(file_path)).is_absolute():
            # abs path must be in one of the workspace folders
            if not any(
                file_path.is_relative_to(folder.path)
                for folder in self.workspace.values()
            ):
                raise ValueError(f"{file_path} is not a valid workspace file path")

            return file_path.as_uri()
        elif len(self.workspace) == 1:  # single root workspace
            folder = self.workspace[ROOT_FOLDER_NAME]
        else:  # multi-root workspace
            if (root := file_path.parts[0]) not in self.workspace:
                raise ValueError(f"{root} is not a valid workspace folder")
            folder = self.workspace[root]

        return AbsPath(file_path, base_path=folder.path).as_uri()

    @override
    def from_uri(self, uri: str) -> AbsPath:
        """Convert a URI to an absolute file path."""
        return from_local_uri(uri)

    @override
    @asynccontextmanager
    async def open_files(self, *file_paths: AnyPath):
        """
        Open files in the LSP client.

        Usually, file-change operations will automatically open the files, perform the operations, and close the files.

        If you know for sure that a set of files will be used in the following requests, you can pre-open them using this method. This will help to reduce the overhead of opening and closing files repeatedly.

        Args:
            file_paths(Sequence[AnyPath]): The file paths to open.
        """

        # do not sync file if specified
        if not self.sync_file:
            yield
            return

        file_uris = [self.as_uri(file_path) for file_path in file_paths]

        if not file_uris:
            yield
            return

        buffer_items = self.file_buffer.open(file_uris)
        await aiometer.run_all(
            [
                partial(
                    self.notify_text_document_opened,
                    file_path=item.file_path,
                    file_content=item.content,
                )
                for item in buffer_items
            ]
        )

        try:
            yield
        finally:
            closed_items = self.file_buffer.close(
                item.file_uri for item in buffer_items
            )
            await aiometer.run_all(
                [
                    partial(
                        self.notify_text_document_closed,
                        file_path=item.file_path,
                    )
                    for item in closed_items
                ]
            )

    @override
    async def _request[R](
        self,
        req: attrs.AttrsInstance,
        schema: type[jsonrpc.Response[R]],
        *,
        file_paths: Sequence[AnyPath] = (),
    ) -> R:
        async with self.open_files(*file_paths):
            req = jsonrpc.request_serialize(req)
            with anyio.fail_after(self.pending_timeout):
                raw_resp = await self.server._request(req)
            return jsonrpc.response_deserialize(raw_resp, schema)

    @override
    async def _notify(self, msg: Notification) -> None:
        noti = jsonrpc.notification_serialize(msg)
        with anyio.fail_after(self.pending_timeout):
            await self.server._notify(noti)

    async def _initialize(self, params: types.InitializeParams):
        """Initialize parameters for the LSP client."""

        result = await self._request(
            types.InitializeRequest(id="initialize", params=params),
            schema=types.InitializeResponse,
        )

        # check for server capabilities
        cls = self.__class__
        for cap_cls in cls.mro():
            if (
                not issubclass(cap_cls, LSPCapabilityProtocol)
                or cap_cls is LSPCapabilityProtocol
                or cap_cls is cls
            ):
                continue

            cap_cls.check_server_capability(
                result.capabilities,
                result.server_info,
            )
            for method in cap_cls.method():
                logger.debug("Server support for {} checked", method)

        self.check_server_compatibility(result.server_info)

        await self._notify(
            types.InitializedNotification(
                params=types.InitializedParams(),
            )
        )

    async def _shutdown(self):
        """
        `shutdown` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#shutdown
        """

        _ = await self._request(
            types.ShutdownRequest(
                id="shutdown",
            ),
            schema=types.ShutdownResponse,
        )

    async def _exit(self) -> None:
        """
        `exit` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#exit
        """

        await self._notify(types.ExitNotification())
