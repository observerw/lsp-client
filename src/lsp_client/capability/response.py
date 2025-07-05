"""
Request/Notification sent from server to client.
"""

from __future__ import annotations

from typing import Protocol, override, runtime_checkable

from lsprotocol import types

from .client import LSPCapabilityClient


@runtime_checkable
class WithReceiveLogMessage(LSPCapabilityClient, Protocol):
    """
    `window/logMessage` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#window_logMessage
    """

    @override
    @classmethod
    def check_client_capability(cls):
        return

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        return

    async def receive_log_message(self, req: types.LogMessageNotification):
        self.logger.debug("Received log message: %s", req.params.message)


@runtime_checkable
class WithReceiveLogTrace(LSPCapabilityClient, Protocol):
    """
    Window log trace capability

    `window/logTrace` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#logTrace
    """

    @override
    @classmethod
    def check_client_capability(cls):
        return

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        return

    async def receive_log_trace(self, req: types.LogTraceNotification):
        self.logger.debug("Received log trace: %s", req.params.message)


@runtime_checkable
class WithReceiveShowMessage(LSPCapabilityClient, Protocol):
    """
    `window/showMessage` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#window_showMessage
    """

    @override
    @classmethod
    def check_client_capability(cls):
        return

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        return

    async def receive_show_message(self, req: types.ShowMessageNotification):
        self.logger.debug("Received show message: %s", req.params.message)


@runtime_checkable
class WithRespondShowMessage(LSPCapabilityClient, Protocol):
    """
    `window/showMessageRequest` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#window_showMessageRequest
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (window := cls.client_capabilities.window)
        assert window.show_message

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        return

    async def respond_show_message(
        self, req: types.ShowMessageRequest
    ) -> types.ShowMessageResponse:
        self.logger.debug("Responding to show message: %s", req.params.message)
        # default to just return None
        return types.ShowMessageResponse(id=req.id)
