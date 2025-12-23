from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

import lsprotocol.types as lsp_type
from loguru import logger

from lsp_client.protocol import (
    CapabilityClientProtocol,
    ServerRequestHook,
    ServerRequestHookProtocol,
    ServerRequestHookRegistry,
    WindowCapabilityProtocol,
)


@runtime_checkable
class WithRespondShowDocumentRequest(
    WindowCapabilityProtocol,
    ServerRequestHookProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `window/showDocument` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#window_showDocument
    """

    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (lsp_type.WINDOW_SHOW_DOCUMENT,)

    @override
    @classmethod
    def register_window_capability(cls, cap: lsp_type.WindowClientCapabilities) -> None:
        super().register_window_capability(cap)
        cap.show_document = lsp_type.ShowDocumentClientCapabilities(True)

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)

    async def respond_show_document_request(
        self, req: lsp_type.ShowDocumentRequest
    ) -> lsp_type.ShowDocumentResponse:
        params = req.params
        logger.debug(
            "Responding to show document: uri={}, external={}, takeFocus={}",
            params.uri,
            params.external,
            params.take_focus,
        )

        # TODO add resonable default behavior

        return lsp_type.ShowDocumentResponse(
            id=req.id,
            result=lsp_type.ShowDocumentResult(success=True),
        )

    @override
    def register_server_request_hooks(
        self, registry: ServerRequestHookRegistry
    ) -> None:
        super().register_server_request_hooks(registry)
        registry.register(
            lsp_type.WINDOW_SHOW_DOCUMENT,
            ServerRequestHook(
                cls=lsp_type.ShowDocumentRequest,
                execute=self.respond_show_document_request,
            ),
        )
