from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

from lsprotocol import types

from lsp_client.types import AnyPath

from .client import LSPCapabilityClient

logger = logging.getLogger(__name__)


@runtime_checkable
class WithNotifyTextDocumentSynchronize(LSPCapabilityClient, Protocol):
    """
    `textDocument/didOpen` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_didOpen
    `textDocument/didChange` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_didChange
    `textDocument/didClose` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_didClose
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.synchronization

        logger.debug("Client supports for textDocument/didOpen checked")
        logger.debug("Client supports for textDocument/didChange checked")
        logger.debug("Client supports for textDocument/didClose checked")

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert capability.text_document_sync

        logger.debug("Server supports textDocument/didOpen checked")
        logger.debug("Server supports textDocument/didChange checked")
        logger.debug("Server supports textDocument/didClose checked")

    async def notify_text_document_opened(
        self, file_path: AnyPath, file_content: str
    ) -> None:
        await self.notify_all(
            msg=types.DidOpenTextDocumentNotification(
                params=types.DidOpenTextDocumentParams(
                    text_document=types.TextDocumentItem(
                        uri=self.as_uri(file_path),
                        language_id=self.language_id,
                        version=0,  # Version 0 for the initial open
                        text=file_content,
                    )
                )
            )
        )

    async def notify_text_document_closed(self, file_path: AnyPath) -> None:
        await self.notify_all(
            types.DidCloseTextDocumentNotification(
                params=types.DidCloseTextDocumentParams(
                    text_document=types.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                )
            )
        )


@runtime_checkable
class WithNotifyChangeConfiguration(LSPCapabilityClient, Protocol):
    """
    `workspace/didChangeConfiguration` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_didChangeConfiguration
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (workspace := cls.client_capabilities.workspace)
        assert workspace.did_change_configuration

        logger.debug("Client supports for workspace/didChangeConfiguration checked")

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        logger.debug("Server supports workspace/didChangeConfiguration checked")

    async def notify_change_configuration(
        self, settings: types.ConfigurationParams
    ) -> None:
        return await self.notify_all(
            types.DidChangeConfigurationNotification(
                params=types.DidChangeConfigurationParams(settings=settings)
            ),
        )


@runtime_checkable
class WithNotifyChangeWorkspaceFolders(LSPCapabilityClient, Protocol):
    """
    `workspace/didChangeWorkspaceFolders` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_didChangeWorkspaceFolders
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (workspace := cls.client_capabilities.workspace)
        assert workspace.workspace_folders

        logger.debug("Client supports for workspace/didChangeWorkspaceFolders checked")

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert (workspace := capability.workspace)
        assert workspace.workspace_folders
        assert workspace.workspace_folders.supported

        logger.debug("Server supports workspace/didChangeWorkspaceFolders checked")

    async def notify_change_workspace_folders(
        self,
        added: Sequence[types.WorkspaceFolder],
        removed: Sequence[types.WorkspaceFolder],
    ) -> None:
        return await self.notify_all(
            types.DidChangeWorkspaceFoldersNotification(
                params=types.DidChangeWorkspaceFoldersParams(
                    event=types.WorkspaceFoldersChangeEvent(
                        added=added,
                        removed=removed,
                    )
                )
            ),
        )
