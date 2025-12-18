from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

from lsp_client.protocol import CapabilityClientProtocol, TextDocumentCapabilityProtocol
from lsp_client.utils.types import AnyPath, lsp_type


@runtime_checkable
class WithNotifyTextDocumentSynchronize(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/didOpen` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_didOpen
    `textDocument/didChange` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_didChange
    `textDocument/didClose` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_didClose
    """

    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (
            lsp_type.TEXT_DOCUMENT_DID_OPEN,
            lsp_type.TEXT_DOCUMENT_DID_CHANGE,
            lsp_type.TEXT_DOCUMENT_DID_CLOSE,
        )

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        cap.synchronization = lsp_type.TextDocumentSyncClientCapabilities(
            will_save=True,
            will_save_wait_until=True,
            did_save=True,
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        cap: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ) -> None:
        super().check_server_capability(cap, info)
        assert cap.text_document_sync

    async def notify_text_document_opened(
        self, file_path: AnyPath, file_content: str
    ) -> None:
        await self.notify(
            msg=lsp_type.DidOpenTextDocumentNotification(
                params=lsp_type.DidOpenTextDocumentParams(
                    text_document=lsp_type.TextDocumentItem(
                        uri=self.as_uri(file_path),
                        language_id=self.get_language_id(),
                        version=0,  # Version 0 for the initial open
                        text=file_content,
                    )
                )
            )
        )

    async def notify_text_document_closed(self, file_path: AnyPath) -> None:
        await self.notify(
            msg=lsp_type.DidCloseTextDocumentNotification(
                params=lsp_type.DidCloseTextDocumentParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                )
            )
        )
