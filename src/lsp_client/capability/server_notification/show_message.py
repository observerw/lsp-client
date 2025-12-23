from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

import lsprotocol.types as lsp_type
from loguru import logger

from lsp_client.protocol import (
    CapabilityClientProtocol,
    ServerNotificationHook,
    ServerRequestHookProtocol,
    ServerRequestHookRegistry,
    WindowCapabilityProtocol,
)


@runtime_checkable
class WithReceiveShowMessage(
    WindowCapabilityProtocol,
    ServerRequestHookProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `window/showMessage` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#window_showMessage
    """

    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (lsp_type.WINDOW_SHOW_MESSAGE,)

    @override
    @classmethod
    def register_window_capability(cls, cap: lsp_type.WindowClientCapabilities) -> None:
        super().register_window_capability(cap)
        cap.show_message = lsp_type.ShowMessageRequestClientCapabilities(
            message_action_item=lsp_type.ClientShowMessageActionItemOptions(
                additional_properties_support=True
            )
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)

    async def receive_show_message(
        self, noti: lsp_type.ShowMessageNotification
    ) -> None:
        logger.info("Received show message: {}", noti.params.message)

    @override
    def register_server_request_hooks(
        self, registry: ServerRequestHookRegistry
    ) -> None:
        super().register_server_request_hooks(registry)
        registry.register(
            lsp_type.WINDOW_SHOW_MESSAGE,
            ServerNotificationHook(
                cls=lsp_type.ShowMessageNotification,
                execute=self.receive_show_message,
            ),
        )
