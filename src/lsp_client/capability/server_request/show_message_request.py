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
class WithRespondShowMessageRequest(
    WindowCapabilityProtocol,
    ServerRequestHookProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `window/showMessageRequest` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#window_showMessageRequest
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (lsp_type.WINDOW_SHOW_MESSAGE_REQUEST,)

    @override
    @classmethod
    def register_window_capability(cls, cap: lsp_type.WindowClientCapabilities) -> None:
        super().register_window_capability(cap)
        cap.show_message = lsp_type.ShowMessageRequestClientCapabilities(
            message_action_item=lsp_type.ClientShowMessageActionItemOptions(
                additional_properties_support=True,
            )
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)

    async def _respond_show_message(
        self, params: lsp_type.ShowMessageRequestParams
    ) -> lsp_type.MessageActionItem | None:
        logger.debug("Responding to show message: {}", params.message)

        # TODO add reasonable default behavior

        return lsp_type.MessageActionItem(title="Default response from `lsp-client`.")

    async def respond_show_message_request(
        self, req: lsp_type.ShowMessageRequest
    ) -> lsp_type.ShowMessageResponse:
        return lsp_type.ShowMessageResponse(
            id=req.id,
            result=await self._respond_show_message(req.params),
        )

    @override
    def register_server_request_hooks(
        self, registry: ServerRequestHookRegistry
    ) -> None:
        super().register_server_request_hooks(registry)
        registry.register(
            lsp_type.WINDOW_SHOW_MESSAGE_REQUEST,
            ServerRequestHook(
                cls=lsp_type.ShowMessageRequest,
                execute=self.respond_show_message_request,
            ),
        )
