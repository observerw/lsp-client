from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

from lsprotocol import types

from lsp_client.types import AnyPath

from .client import LSPCapabilityClient


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

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert capability.text_document_sync

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
class WithNotifyPublishDiagnostics(LSPCapabilityClient, Protocol):
    """
    Publish diagnostics capability.

    `textDocument/publishDiagnostics` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_publishDiagnostics

    The publish diagnostics notification is sent from the server to the client to
    provide diagnostics information for a text document.
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.publish_diagnostics

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        return

    async def notify_publish_diagnostics(
        self, file_path: AnyPath, diagnostics: Sequence[types.Diagnostic]
    ) -> None:
        await self.notify_all(
            types.PublishDiagnosticsNotification(
                params=types.PublishDiagnosticsParams(
                    uri=self.as_uri(file_path),
                    diagnostics=diagnostics,
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

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        return

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

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert (workspace := capability.workspace)
        assert workspace.workspace_folders
        assert workspace.workspace_folders.supported

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
