from __future__ import annotations

from collections.abc import Iterator
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
class WithReceiveLogTrace(
    WindowCapabilityProtocol,
    ServerRequestHookProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `$/logTrace` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#logTrace
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (lsp_type.LOG_TRACE,)

    @override
    @classmethod
    def register_window_capability(cls, cap: lsp_type.WindowClientCapabilities) -> None:
        super().register_window_capability(cap)

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)

    async def _receive_log_trace(self, params: lsp_type.LogTraceParams) -> None:
        logger.info("Received log trace: {}", params.message)

    async def receive_log_trace(self, noti: lsp_type.LogTraceNotification) -> None:
        return await self._receive_log_trace(noti.params)

    @override
    def register_server_request_hooks(
        self, registry: ServerRequestHookRegistry
    ) -> None:
        super().register_server_request_hooks(registry)
        registry.register(
            lsp_type.LOG_TRACE,
            ServerNotificationHook(
                cls=lsp_type.LogTraceNotification,
                execute=self.receive_log_trace,
            ),
        )
