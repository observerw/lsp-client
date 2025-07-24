from __future__ import annotations

import logging
from abc import abstractmethod
from collections.abc import Sequence
from typing import Any, Protocol, final, runtime_checkable

from lsprotocol import types

from lsp_client.jsonrpc import JsonRpcResponse
from lsp_client.types import AnyPath
from lsp_client.utils.path import AbsPath


@runtime_checkable
class LSPCapabilityProtocol(Protocol):
    @classmethod
    @abstractmethod
    def client_capability(cls) -> types.ClientCapabilities:
        """
        Return the client capabilities for this capability.
        This is used to register the capability with the LSP server.
        """

    @classmethod
    @abstractmethod
    def check_server_capability(
        cls,
        capability: types.ServerCapabilities,
        info: types.ServerInfo | None,
    ):
        """
        Check if the server supports this capability.
        This is used to validate the server capabilities against the client capabilities.
        """


@runtime_checkable
class LSPCapabilityClientProtocol(Protocol):
    """
    Minimal interface to implement LSP capabilities.

    This abstract base class provides the foundation for implementing various
    Language Server Protocol capabilities. Concrete implementations should
    inherit from this class along with specific capability mixins.
    """

    @property
    def repo_path(self) -> AbsPath: ...

    @property
    def logger(self) -> logging.Logger: ...

    @property
    def language_id(self) -> types.LanguageKind: ...

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
        ...

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
        ...

    async def respond(self, resp: Any):
        """
        Respond the request from the LSP server.

        Args:
            resp (Any): The response to send back to the LSP server.
        """

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
