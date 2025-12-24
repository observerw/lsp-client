from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, override, runtime_checkable

from loguru import logger

from lsp_client.protocol import (
    CapabilityClientProtocol,
    ServerRequestHook,
    ServerRequestHookProtocol,
    ServerRequestHookRegistry,
    WindowCapabilityProtocol,
)
from lsp_client.utils.types import lsp_type


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
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (lsp_type.WINDOW_SHOW_DOCUMENT,)

    @override
    @classmethod
    def register_window_capability(cls, cap: lsp_type.WindowClientCapabilities) -> None:
        super().register_window_capability(cap)
        cap.show_document = lsp_type.ShowDocumentClientCapabilities(True)

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)

    async def _respond_show_document(
        self, params: lsp_type.ShowDocumentParams
    ) -> lsp_type.ShowDocumentResult:
        logger.debug(
            "Responding to show document: uri={}, external={}, takeFocus={}",
            params.uri,
            params.external,
            params.take_focus,
        )

        # TODO add resonable default behavior

        return lsp_type.ShowDocumentResult(success=True)

    async def respond_show_document_request(
        self, req: lsp_type.ShowDocumentRequest
    ) -> lsp_type.ShowDocumentResponse:
        return lsp_type.ShowDocumentResponse(
            id=req.id,
            result=await self._respond_show_document(req.params),
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
