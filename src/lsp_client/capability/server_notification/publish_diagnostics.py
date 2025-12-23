from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

import lsprotocol.types as lsp_type
from loguru import logger

from lsp_client.protocol import (
    CapabilityClientProtocol,
    ServerRequestHookProtocol,
    ServerRequestHookRegistry,
    TextDocumentCapabilityProtocol,
)
from lsp_client.protocol.hook import ServerNotificationHook


@runtime_checkable
class WithReceivePublishDiagnostics(
    TextDocumentCapabilityProtocol,
    ServerRequestHookProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/publishDiagnostics` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_publishDiagnostics
    """

    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (lsp_type.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS,)

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        super().register_text_document_capability(cap)
        cap.diagnostic = lsp_type.DiagnosticClientCapabilities(
            related_document_support=True,
            related_information=True,
            tag_support=lsp_type.ClientDiagnosticsTagOptions(
                value_set=[*lsp_type.DiagnosticTag]
            ),
            code_description_support=True,
            data_support=True,
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)

    async def receive_publish_diagnostics(
        self, noti: lsp_type.PublishDiagnosticsNotification
    ) -> None:
        logger.debug(
            "Received diagnostics for {}: {}",
            noti.params.uri,
            noti.params.diagnostics,
        )

    @override
    def register_server_request_hooks(
        self, registry: ServerRequestHookRegistry
    ) -> None:
        super().register_server_request_hooks(registry)
        registry.register(
            lsp_type.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS,
            ServerNotificationHook(
                cls=lsp_type.PublishDiagnosticsNotification,
                execute=self.receive_publish_diagnostics,
            ),
        )
