from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

import lsprotocol.types as lsp_type
from loguru import logger

from lsp_client.protocol import (
    CapabilityClientProtocol,
    ServerRequestHookProtocol,
    ServerRequestHookRegistry,
    WindowCapabilityProtocol,
)
from lsp_client.protocol.hook import ServerNotificationHook


@runtime_checkable
class WithReceiveLogMessage(
    WindowCapabilityProtocol,
    ServerRequestHookProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `window/logMessage` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#window_logMessage
    """

    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (lsp_type.WINDOW_LOG_MESSAGE,)

    @override
    @classmethod
    def register_window_capability(cls, cap: lsp_type.WindowClientCapabilities) -> None:
        super().register_window_capability(cap)

    @override
    @classmethod
    def check_server_capability(
        cls,
        cap: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ) -> None:
        super().check_server_capability(cap, info)

    async def receive_log_message(self, noti: lsp_type.LogMessageNotification) -> None:
        logger.info("Received log message: {}", noti.params.message)

    @override
    def register_server_request_hooks(
        self, registry: ServerRequestHookRegistry
    ) -> None:
        super().register_server_request_hooks(registry)
        registry.register(
            lsp_type.WINDOW_LOG_MESSAGE,
            ServerNotificationHook(
                cls=lsp_type.LogMessageNotification,
                execute=self.receive_log_message,
            ),
        )
