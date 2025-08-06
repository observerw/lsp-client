from __future__ import annotations

import asyncio as aio
import os
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import cached_property
from itertools import product
from pathlib import Path
from typing import Any, Self, final, override

import attrs
from asyncio_addon import gather_all
from loguru import logger
from lsprotocol import types

import lsp_client.capability as lsp_cap
from lsp_client import jsonrpc, lsp_type
from lsp_client.types import AnyPath, Notification
from lsp_client.utils.attrs import attrs_merges
from lsp_client.utils.path import AbsPath

from .file_buffer import LSPFileBuffer
from .notification import WithNotifyTextDocumentSynchronize
from .protocol import LSPCapabilityClientProtocol, LSPCapabilityProtocol

ROOT_FOLDER_NAME = "__root__"


@attrs.define
class WorkspaceFolder(lsp_type.WorkspaceFolder):
    @cached_property
    def path(self) -> AbsPath:
        return AbsPath.from_uri(self.uri)


@final
@dataclass(frozen=True)
class ClientRuntimeArgs:
    server_count: int
    sender: jsonrpc.RequestSender
    receiver: jsonrpc.RequestReceiver
    workspace_folders: Sequence[WorkspaceFolder]


@dataclass(frozen=True)
class ClientArgs:
    sync_file: bool = True
    """Whether to synchronize file (open, close, changed, etc.) when performing file-related operations."""

    pending_timeout: float | None = 10.0
    """Timeout for pending requests."""


@dataclass(kw_only=True)
class LSPCapabilityClientBase[T](
    # Client support for `textDocument/didOpen`, `textDocument/didChange` and `textDocument/didClose`
    # notifications is mandatory
    WithNotifyTextDocumentSynchronize,
    LSPCapabilityClientProtocol,
    ABC,
):
    _runtime: ClientRuntimeArgs
    _args: ClientArgs
    _extra: T | None

    _request_tg: aio.TaskGroup
    """Tasks of sending requests to the server and receiving responses."""

    _closed: bool = False

    @abstractmethod
    def check_server_compatibility(self, info: types.ServerInfo | None):
        """Check if the available server capabilities are compatible with the client."""

    @property
    @override
    def workspace_folders(self) -> Sequence[WorkspaceFolder]:
        return [*self.workspace.values()]

    @cached_property
    def workspace(self) -> dict[str, WorkspaceFolder]:
        """Workspace folders indexed by their URIs."""
        return {folder.name: folder for folder in self._runtime.workspace_folders}

    @cached_property
    def is_single_root(self) -> bool:
        """Whether the workspace has a single root folder."""
        return len(self.workspace) == 1

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

    @property
    def initialization_options(self) -> dict[str, Any]:
        return {}

    @classmethod
    @asynccontextmanager
    async def start(
        cls,
        args: ClientArgs,
        runtime_args: ClientRuntimeArgs,
        *,
        extra: T | None = None,
    ) -> AsyncGenerator[Self, Any]:
        async with aio.TaskGroup() as tg:
            instance = cls(
                _runtime=runtime_args,
                _args=args,
                _extra=extra,
                _request_tg=tg,
            )

            initialize_params = types.InitializeParams(
                capabilities=instance.client_capabilities(),
                process_id=os.getpid(),
                client_info=types.ClientInfo(
                    name="LSP Client",
                    version="1.81.0-insider",
                ),
                locale="en-us",
                initialization_options=instance.initialization_options,
                trace=types.TraceValue.Verbose,
                workspace_folders=runtime_args.workspace_folders,
            )

            # initialize repo
            _ = await instance._initialize(initialize_params)

            # prepare for server side requests
            server_req_worker_task = tg.create_task(instance._server_request_worker())

            try:
                yield instance
                # all client side requests are sent
            finally:
                try:
                    _ = await instance._shutdown()
                except TimeoutError as e:
                    raise TimeoutError(
                        "LSP client shutdown timed out, server failed to exit gracefully."
                    ) from e
                # request server to shutdown (but not exit)

                await instance._runtime.receiver.join()
                assert server_req_worker_task.cancel()
                # all server side requests are handled
            # all client side requests are sent
        # all client side requests are responded
        await instance._exit()  # request server to exit
        instance._closed = True

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

        if self.is_single_root:
            folder = self.workspace[ROOT_FOLDER_NAME]
        else:
            root = file_path.parts[0]
            if root not in self.workspace:
                raise ValueError(f"{root} is not a valid workspace folder")
            folder = self.workspace[root]

        return AbsPath(file_path, base_path=folder.path).as_uri()

    @override
    def from_uri(self, uri: str) -> AbsPath:
        """Convert a URI to an absolute file path."""
        return AbsPath.from_uri(uri)

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
        if not self._args.sync_file:
            yield
            return

        self._check_closed()

        file_uris = [self.as_uri(file_path) for file_path in file_paths]

        if not file_uris:
            yield
            return

        buffer_items = self.file_buffer.open(file_uris)
        await gather_all(
            self.notify_text_document_opened(
                file_path=item.file_path,
                file_content=item.content,
            )
            for item in buffer_items
        )

        try:
            yield
        finally:
            closed_items = self.file_buffer.close(
                item.file_uri for item in buffer_items
            )
            await gather_all(
                self.notify_text_document_closed(file_path=item.file_path)
                for item in closed_items
            )

    @override
    async def request[R](
        self,
        req: attrs.AttrsInstance,
        schema: type[jsonrpc.Response[R]],
        *,
        file_paths: Sequence[AnyPath] = (),
    ) -> R:
        self._check_closed()

        async with self.open_files(*file_paths):
            req = jsonrpc.request_serialize(req)
            tx, rx = jsonrpc.response_channel.create()
            await self._runtime.sender.send((req, tx))
            raw_resp = await rx.receive(timeout=self._args.pending_timeout)
            return jsonrpc.response_deserialize(raw_resp, schema)

    async def _request_many[R](
        self,
        req: attrs.AttrsInstance,
        schema: type[jsonrpc.Response[R]],
    ) -> Sequence[R]:
        """
        This is not a public API. Only use to send `initialize` and `shutdown` request.
        """

        self._check_closed()

        req = jsonrpc.request_serialize(req)
        tx, rx = jsonrpc.many_response_channel.create(
            expect_count=self._runtime.server_count
        )
        await self._runtime.sender.send((req, tx))

        raw_resp = await rx.receive(timeout=self._args.pending_timeout)
        return [jsonrpc.response_deserialize(item, schema) for item in raw_resp]

    @override
    async def notify_all(self, msg: Notification) -> None:
        self._check_closed()

        noti = jsonrpc.notification_serialize(msg)
        await self._runtime.sender.send(noti)

    def create_request[Task](self, coro: aio._CoroutineLike[Task]) -> aio.Task[Task]:
        self._check_closed()

        return self._request_tg.create_task(coro)

    async def _initialize(self, params: types.InitializeParams):
        """Initialize parameters for the LSP client."""

        results = await self._request_many(
            types.InitializeRequest(id="intialize", params=params),
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

            self.check_server_compatibility(result.server_info)

        await self.notify_all(
            types.InitializedNotification(
                params=types.InitializedParams(),
            )
        )

    async def _shutdown(self):
        """
        `shutdown` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#shutdown
        """

        await self._request_many(
            types.ShutdownRequest(
                id="shutdown",
            ),
            schema=types.ShutdownResponse,
        )

    async def _exit(self) -> None:
        """
        `exit` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#exit
        """

        await self.notify_all(types.ExitNotification())

    async def _dispatch_server_request(self, req: jsonrpc.ChannelRequest):
        match req:
            case {"method": types.WINDOW_LOG_MESSAGE} if isinstance(
                self, lsp_cap.WithReceiveLogMessage
            ):
                await self.receive_log_message(
                    jsonrpc.request_deserialize(req, lsp_type.LogMessageNotification)
                )
            case {"method": types.WINDOW_SHOW_MESSAGE} if isinstance(
                self, lsp_cap.WithReceiveShowMessage
            ):
                await self.receive_show_message(
                    jsonrpc.request_deserialize(req, lsp_type.ShowMessageNotification)
                )
            case ({"method": types.WINDOW_SHOW_MESSAGE_REQUEST} as raw_req, tx) if (
                isinstance(self, lsp_cap.WithRespondShowMessageRequest)
            ):
                resp = await self.respond_show_message(
                    jsonrpc.request_deserialize(raw_req, lsp_type.ShowMessageRequest)
                )
                tx.send(jsonrpc.response_serialize(resp))
            case {"method": types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS} if isinstance(
                self, lsp_cap.WithReceivePublishDiagnostics
            ):
                await self.receive_publish_diagnostics(
                    jsonrpc.request_deserialize(
                        req, lsp_type.PublishDiagnosticsNotification
                    )
                )
            case ({"method": types.WORKSPACE_WORKSPACE_FOLDERS} as raw_req, tx) if (
                isinstance(self, lsp_cap.WithRespondWorkspaceFolders)
            ):
                resp = await self.respond_workspace_folders(
                    jsonrpc.request_deserialize(
                        raw_req, lsp_type.WorkspaceFoldersRequest
                    )
                )
                tx.send(jsonrpc.response_serialize(resp))
            case (
                {"method": types.WORKSPACE_CONFIGURATION} as raw_req,
                tx,
            ) if isinstance(self, lsp_cap.WithRespondWorkspaceConfiguration):
                resp = await self.respond_workspace_configuration(
                    jsonrpc.request_deserialize(raw_req, lsp_type.ConfigurationRequest)
                )
                tx.send(jsonrpc.response_serialize(resp))
            case (raw_req, _):
                # if server sent a request that client can't handle, raise an error
                raise ValueError(f"Unexpected server-side request: {raw_req}")
            case noti:
                logger.warning("Unknown notification: {}", noti)

        self._runtime.receiver.task_done()

    async def _server_request_worker(self):
        async with aio.TaskGroup() as tg:
            while req := await self._runtime.receiver.receive():
                tg.create_task(self._dispatch_server_request(req))
