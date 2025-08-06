from __future__ import annotations

import asyncio as aio
import os
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Mapping, Sequence
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
from lsp_client.capability.file_buffer import LSPFileBuffer
from lsp_client.capability.notification import WithNotifyTextDocumentSynchronize
from lsp_client.capability.protocol import (
    LSPCapabilityClientProtocol,
    LSPCapabilityProtocol,
)
from lsp_client.server.base import LSPServerBase
from lsp_client.types import AnyPath, Notification, Workspace, WorkspaceFolder
from lsp_client.utils.attrs import attrs_merges
from lsp_client.utils.path import AbsPath

ROOT_FOLDER_NAME = "__root__"


@final
@dataclass(frozen=True)
class ClientRuntime:
    server: LSPServerBase
    workspace: Workspace
    tg: aio.TaskGroup


@dataclass(kw_only=True)
class LSPClientBase(
    # Client support for `textDocument/didOpen`, `textDocument/didChange` and `textDocument/didClose`
    # notifications is mandatory
    WithNotifyTextDocumentSynchronize,
    LSPCapabilityClientProtocol,
    ABC,
):
    _runtime: ClientRuntime | None = None

    sync_file: bool = True
    """Whether to synchronize file (open, close, changed, etc.) when performing file-related operations."""

    pending_timeout: float | None = 10.0
    """Timeout for pending requests."""

    @abstractmethod
    def create_server(self) -> LSPServerBase: ...

    @abstractmethod
    def create_initialization_options(self) -> dict[str, Any] | None: ...

    @abstractmethod
    def check_server_compatibility(self, info: types.ServerInfo | None):
        """Check if the available server capabilities are compatible with the client."""

    @property
    def runtime(self) -> ClientRuntime:
        if not (runtime := self._runtime):
            raise RuntimeError("Client is closed.")

        return runtime

    @property
    @override
    def workspace_folders(self) -> Sequence[WorkspaceFolder]:
        return [*self.runtime.workspace.values()]

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

    @asynccontextmanager
    async def start(
        self, workspace: AnyPath | Mapping[str, AnyPath]
    ) -> AsyncGenerator[Self]:
        match workspace:
            case str() | os.PathLike() as root_folder_path:
                formatted_workspace = {
                    ROOT_FOLDER_NAME: WorkspaceFolder(
                        uri=AbsPath(root_folder_path).as_uri(),
                        name=ROOT_FOLDER_NAME,
                    )
                }
            case _ as mapping:
                formatted_workspace = {
                    name: WorkspaceFolder(uri=AbsPath(path).as_uri(), name=name)
                    for name, path in mapping.items()
                }

        server = self.create_server()
        async with server.serve(workspace=formatted_workspace) as server:
            async with aio.TaskGroup() as tg:
                self._runtime = ClientRuntime(
                    server=server,
                    workspace=formatted_workspace,
                    tg=tg,
                )

                initialize_params = types.InitializeParams(
                    capabilities=self.client_capabilities(),
                    process_id=os.getpid(),
                    client_info=types.ClientInfo(
                        name="LSP Client",
                        version="1.81.0-insider",
                    ),
                    locale="en-us",
                    initialization_options=self.create_initialization_options(),
                    trace=types.TraceValue.Verbose,
                    workspace_folders=self.workspace_folders,
                )

                # initialize repo
                _ = await self._initialize(initialize_params)

                # prepare for server side requests
                server_req_worker_task = tg.create_task(self._server_request_worker())

                try:
                    yield self
                    # all client side requests are sent
                finally:
                    try:
                        _ = await self._shutdown()
                    except TimeoutError as e:
                        raise TimeoutError(
                            "LSP client shutdown timed out, server failed to exit gracefully."
                        ) from e
                    # request server to shutdown (but not exit)

                    await self.runtime.server.server_request_receiver.join()
                    canceled = server_req_worker_task.cancel()
                    assert canceled, "Server request worker task is not canceled"
                    # all server side requests are handled
                # all client side requests are sent
            # all client side requests are responded
            await self._exit()  # request server to exit

    # all server processes are exited

    @cached_property
    def file_buffer(self) -> LSPFileBuffer:
        return LSPFileBuffer()

    @override
    def as_uri(self, file_path: AnyPath) -> str:
        """
        Turn a file path into a URI.

        For multi-root workspace, using the first part of a relative path as the workspace folder name.
        """

        workspace = self.runtime.workspace

        if (file_path := Path(file_path)).is_absolute():
            # abs path must be in one of the workspace folders
            if not any(
                file_path.is_relative_to(folder.path) for folder in workspace.values()
            ):
                raise ValueError(f"{file_path} is not a valid workspace file path")

            return file_path.as_uri()

        if len(self.runtime.workspace) == 1:  # single root workspace
            folder = workspace[ROOT_FOLDER_NAME]
        else:
            if (root := file_path.parts[0]) not in workspace:
                raise ValueError(f"{root} is not a valid workspace folder")
            folder = workspace[root]

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
        if not self.sync_file:
            yield
            return

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

    def create_request[Task](self, coro: aio._CoroutineLike[Task]) -> aio.Task[Task]:
        return self.runtime.tg.create_task(
            aio.wait_for(coro, timeout=self.pending_timeout)
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
            raw_resp = await aio.wait_for(
                self.runtime.server.request(req),
                timeout=self.pending_timeout,
            )
            return jsonrpc.response_deserialize(raw_resp, schema)

    async def _request_all[R](
        self,
        req: attrs.AttrsInstance,
        schema: type[jsonrpc.Response[R]],
    ) -> Sequence[R]:
        """
        This is not a public API. Only use to send `initialize` and `shutdown` request.
        """

        req = jsonrpc.request_serialize(req)
        raw_resp = await aio.wait_for(
            self.runtime.server.request_all(req),
            timeout=self.pending_timeout,
        )
        return [jsonrpc.response_deserialize(item, schema) for item in raw_resp]

    @override
    async def _notify(self, msg: Notification) -> None:
        noti = jsonrpc.notification_serialize(msg)
        await aio.wait_for(
            self.runtime.server.notify(noti),
            timeout=self.pending_timeout,
        )

    async def _initialize(self, params: types.InitializeParams):
        """Initialize parameters for the LSP client."""

        results = await self._request_all(
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

        await self._notify(
            types.InitializedNotification(
                params=types.InitializedParams(),
            )
        )

    async def _shutdown(self):
        """
        `shutdown` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#shutdown
        """

        _ = await self._request_all(
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

        self.runtime.server.server_request_receiver.task_done()

    async def _server_request_worker(self):
        async with aio.TaskGroup() as tg:
            while req := await self.runtime.server.server_request_receiver.receive():
                tg.create_task(
                    aio.wait_for(
                        self._dispatch_server_request(req),
                        timeout=self.pending_timeout,
                    )
                )
