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
    def methods(cls) -> Sequence[str]:
        return (lsp_type.WINDOW_SHOW_MESSAGE_REQUEST,)

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

    async def respond_show_message_request(
        self, req: lsp_type.ShowMessageRequest
    ) -> lsp_type.ShowMessageResponse:
        params = req.params
        logger.debug("Responding to show message: {}", params.message)

        # TODO add reasonable default behavior

        return lsp_type.ShowMessageResponse(
            id=req.id,
            result=lsp_type.MessageActionItem(
                title="Default response from `lsp-client`."
            ),
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
