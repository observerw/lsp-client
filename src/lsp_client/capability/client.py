from __future__ import annotations

import logging
import os
from abc import abstractmethod
from collections.abc import Sequence
from functools import cached_property
from typing import Any, ClassVar, Protocol, final

from lsprotocol import types

from lsp_client.jsonrpc import JsonRpcResponse
from lsp_client.types import AnyPath
from lsp_client.utils.path import AbsPath


class LSPCapability(Protocol):
    @classmethod
    @abstractmethod
    def check_client_capability(cls): ...

    @classmethod
    @abstractmethod
    def check_server_capability(cls, capability: types.ServerCapabilities): ...


class LSPCapabilityClient(LSPCapability, Protocol):
    """
    Minimal interface to implement LSP capabilities.

    This abstract base class provides the foundation for implementing various
    Language Server Protocol capabilities. Concrete implementations should
    inherit from this class along with specific capability mixins.
    """

    repo_path: AbsPath
    logger: logging.Logger

    language_id: ClassVar[types.LanguageKind]
    client_capabilities: ClassVar[types.ClientCapabilities]
    initialization_options: ClassVar[dict | None] = None

    @cached_property
    def initialize_params(self) -> types.InitializeParams:
        """Initialize parameters for the LSP client."""
        root_uri = self.repo_path.as_uri()
        root_path_posix = self.repo_path.as_posix()

        return types.InitializeParams(
            capabilities=self.client_capabilities,
            process_id=os.getpid(),
            client_info=types.ClientInfo(
                name="LSP Client",
                version="1.81.0-insider",
            ),
            locale="en-us",
            root_path=root_path_posix,
            root_uri=root_uri,
            initialization_options=self.initialization_options,
            trace=types.TraceValue.Verbose,
            workspace_folders=[
                types.WorkspaceFolder(
                    uri=root_uri,
                    name=self.repo_path.name,
                )
            ],
        )

    @classmethod
    def check_version_capability(cls):
        """
        Check if the LSP server version is compatible with the client capabilities.

        Override this method in concrete implementations to enforce version checks.
        """

    @abstractmethod
    async def request[R](
        self,
        req: Any,
        schema: type[JsonRpcResponse[R]],
        *,
        file_paths: Sequence[AnyPath] = ...,
    ) -> R:
        """Send a request to the LSP server.

        Args:
            method (str): The LSP method to call.
            schema (type[T]): The `attrs` schema for the response, provided by `lsprotocol.types`.
            params (Any | None, optional): The parameters for the method. Defaults to None.
            id (JsonRpcID): The ID for the request, used to match responses. Defaults to a `uuid4` ID.
            file_paths (Sequence[AnyPath], optional): Files to associate with the request, if any. Defaults to an empty sequence.

        Returns:
            T: The response from the LSP server.
        """

    @abstractmethod
    async def request_all[R](
        self,
        req: Any,
        schema: type[JsonRpcResponse[R]],
        *,
        file_paths: Sequence[AnyPath] = ...,
    ) -> Sequence[R]:
        """
        Send a request to all LSP servers. Only used for methods that needs to be sent to all servers, such as `initialize` and `shutdown`.

        Returns:
            Sequence[Any]: The responses from all LSP servers.
        """

    @abstractmethod
    async def respond(self, resp: Any):
        """
        Respond the request from the LSP server.

        Args:
            resp (Any): The response to send back to the LSP server.
        """

    @abstractmethod
    async def notify_all(self, msg: Any):
        """
        Notify all LSP servers. Only used for methods that need to be sent to all servers, such as `initialized`.

        Args:
            method (str): The LSP method to call.
            params (Any | None, optional): The parameters for the method. Defaults to None.
        """

    @final
    def as_uri(self, file_path: AnyPath) -> str:
        """Convert any file path to a absolute URI."""
        return AbsPath(file_path, base_path=self.repo_path).as_uri()

    @final
    def from_uri(self, uri: str) -> AbsPath:
        """Convert a URI to an absolute file path."""
        return AbsPath.from_uri(uri)

    async def initialize(self):
        result = await self.request_all(
            types.InitializeRequest(
                id="intialize",
                params=self.initialize_params,
            ),
            schema=types.InitializeResponse,
        )
        for res in result:
            super().check_server_capability(res.capabilities)

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
