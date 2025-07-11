"""
Server-side request/notification.
"""

from __future__ import annotations

import logging
from typing import Protocol, override, runtime_checkable

from lsprotocol import types

from .client import LSPCapabilityClient

logger = logging.getLogger(__name__)


@runtime_checkable
class WithReceiveLogMessage(LSPCapabilityClient, Protocol):
    """
    `window/logMessage` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#window_logMessage
    """

    @override
    @classmethod
    def check_client_capability(cls):
        logger.debug("Client supports window/logMessage checked")

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        logger.debug("Server supports window/logMessage checked")

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
        logger.debug("Client supports window/logTrace checked")

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        logger.debug("Server supports window/logTrace checked")

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
        logger.debug("Client supports window/showMessage checked")

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        logger.debug("Server supports window/showMessage checked")

    async def receive_show_message(self, req: types.ShowMessageNotification):
        self.logger.debug("Received show message: %s", req.params.message)


@runtime_checkable
class WithNotifyPublishDiagnostics(LSPCapabilityClient, Protocol):
    """
    `textDocument/publishDiagnostics` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_publishDiagnostics
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.publish_diagnostics

        logger.debug("Client supports for textDocument/publishDiagnostics checked")

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        logger.debug("Server supports textDocument/publishDiagnostics checked")

    async def notify_publish_diagnostics(
        self,
        req: types.PublishDiagnosticsNotification,
    ) -> None:
        # TODO add support for diagnostic handling
        self.logger.debug(
            "Received publish diagnostics for %s",
            req.params.uri,
        )


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
        logger.debug("Client supports window/showMessageRequest checked")

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        logger.debug("Server supports window/showMessageRequest checked")

    async def respond_show_message(
        self, req: types.ShowMessageRequest
    ) -> types.ShowMessageResponse:
        self.logger.debug("Responding to show message: %s", req.params.message)
        # default to just return None
        return types.ShowMessageResponse(id=req.id)
