from __future__ import annotations

from abc import abstractmethod
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from typing import Protocol, runtime_checkable

from lsp_client import jsonrpc
from lsp_client.types import AnyPath, Notification, Request, lsp_type
from lsp_client.utils.path import AbsPath


@runtime_checkable
class LSPCapabilityProtocol(Protocol):
    """
    Protocol defining the interface for LSP capability implementation.
    """

    @classmethod
    @abstractmethod
    def client_capability(cls) -> lsp_type.ClientCapabilities:
        """
        Return the client capabilities for this capability.
        This is used to register the capability with the LSP server.
        """

    @classmethod
    @abstractmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        """
        Check if the server supports this capability.
        This is used to validate the server capabilities against the client capabilities.
        """


@runtime_checkable
class LSPCapabilityClientProtocol(Protocol):
    """
    Minimal interface for a client to perform LSP operations.
    """

    @property
    @abstractmethod
    def language_id(self) -> lsp_type.LanguageKind: ...

    @property
    @abstractmethod
    def workspace_folders(self) -> Sequence[lsp_type.WorkspaceFolder]: ...

    @abstractmethod
    @asynccontextmanager
    def open_files(self, *file_paths: AnyPath) -> AsyncGenerator[None]:
        """Open files in the client.

        This method is used to indicate that the files are opened in the client.

        Args:
            file_paths (Sequence[AnyPath]): The file paths to open.
        """

    @abstractmethod
    async def _request[R](
        self,
        req: Request,
        schema: type[jsonrpc.Response[R]],
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
    async def _notify(self, msg: Notification):
        """
        Notify all LSP servers. Only used for methods that need to be sent to all servers, such as `initialized`.

        Args:
            method (str): The LSP method to call.
            params (Any | None, optional): The parameters for the method. Defaults to None.
        """

    @abstractmethod
    def as_uri(self, file_path: AnyPath) -> str:
        """Convert any file path to a absolute URI."""

    @abstractmethod
    def from_uri(self, uri: str) -> AbsPath:
        """Convert a URI to an absolute file path."""
