"""
Server-side request/notification.
"""

from __future__ import annotations

import logging
from typing import Protocol, override, runtime_checkable

from lsprotocol import types

from .protocol import LSPCapabilityClientProtocol, LSPCapabilityProtocol

logger = logging.getLogger(__name__)


@runtime_checkable
class WithReceiveLogMessage(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    """
    `window/logMessage` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#window_logMessage
    """

    @override
    @classmethod
    def client_capability(cls) -> types.ClientCapabilities:
        # logMessage don't need client capabilities
        return types.ClientCapabilities()

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: types.ServerCapabilities,
        info: types.ServerInfo | None,
    ):
        logger.debug("Server supports window/logMessage checked")

    async def receive_log_message(self, req: types.LogMessageNotification):
        self.logger.debug("Received log message: %s", req.params.message)


@runtime_checkable
class WithReceiveLogTrace(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    """
    Window log trace capability

    `window/logTrace` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#logTrace
    """

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: types.ServerCapabilities,
        info: types.ServerInfo | None,
    ):
        logger.debug("Server supports window/logTrace checked")

    async def receive_log_trace(self, req: types.LogTraceNotification):
        self.logger.debug("Received log trace: %s", req.params.message)


@runtime_checkable
class WithReceiveShowMessage(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    """
    `window/showMessage` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#window_showMessage
    """

    @override
    @classmethod
    def client_capability(cls) -> types.ClientCapabilities:
        return types.ClientCapabilities(
            window=types.WindowClientCapabilities(
                show_message=types.ShowMessageRequestClientCapabilities(
                    message_action_item=types.ClientShowMessageActionItemOptions(
                        additional_properties_support=True,
                    ),
                ),
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: types.ServerCapabilities,
        info: types.ServerInfo | None,
    ):
        logger.debug("Server supports window/showMessage checked")

    async def receive_show_message(self, req: types.ShowMessageNotification):
        self.logger.debug("Received show message: %s", req.params.message)


@runtime_checkable
class WithNotifyPublishDiagnostics(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/publishDiagnostics` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_publishDiagnostics
    """

    @override
    @classmethod
    def client_capability(cls) -> types.ClientCapabilities:
        return types.ClientCapabilities(
            text_document=types.TextDocumentClientCapabilities(
                publish_diagnostics=types.PublishDiagnosticsClientCapabilities(
                    related_information=True,
                    version_support=True,
                    tag_support=types.ClientDiagnosticsTagOptions(
                        value_set=[types.DiagnosticTag.Deprecated]
                    ),
                    code_description_support=True,
                )
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: types.ServerCapabilities,
        info: types.ServerInfo | None,
    ):
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
class WithRespondShowMessage(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    """
    `window/showMessageRequest` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#window_showMessageRequest
    """

    @override
    @classmethod
    def client_capability(cls) -> types.ClientCapabilities:
        return types.ClientCapabilities(
            window=types.WindowClientCapabilities(
                show_message=types.ShowMessageRequestClientCapabilities(
                    message_action_item=types.ClientShowMessageActionItemOptions(
                        additional_properties_support=True,
                    ),
                ),
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: types.ServerCapabilities,
        info: types.ServerInfo | None,
    ):
        logger.debug("Server supports window/showMessageRequest checked")

    async def respond_show_message(
        self, req: types.ShowMessageRequest
    ) -> types.ShowMessageResponse:
        self.logger.debug("Responding to show message: %s", req.params.message)
        # default to just return None
        return types.ShowMessageResponse(id=req.id)


@runtime_checkable
class WithRespondWorkspaceFolders(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    """
    `workspace/workspaceFolders` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_workspaceFolders
    """

    @override
    @classmethod
    def client_capability(cls) -> types.ClientCapabilities:
        return types.ClientCapabilities(
            workspace=types.WorkspaceClientCapabilities(workspace_folders=True)
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: types.ServerCapabilities,
        info: types.ServerInfo | None,
    ):
        logger.debug("Server supports workspace/workspaceFolders checked")

    async def respond_workspace_folders(
        self, req: types.WorkspaceFoldersRequest
    ) -> types.WorkspaceFoldersResponse:
        self.logger.debug("Responding to workspace folders request")
        # TODO do we need to do something here?
        return types.WorkspaceFoldersResponse(
            id=req.id,
            result=None,
        )


@runtime_checkable
class WithRespondWorkspaceConfiguration(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    """
    `workspace/configuration` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_configuration
    """

    @override
    @classmethod
    def client_capability(cls) -> types.ClientCapabilities:
        return types.ClientCapabilities(
            workspace=types.WorkspaceClientCapabilities(
                configuration=True,
                workspace_folders=True,
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: types.ServerCapabilities,
        info: types.ServerInfo | None,
    ):
        logger.debug("Server supports workspace/configuration checked")

    async def respond_workspace_configuration(
        self, req: types.ConfigurationRequest
    ) -> types.ConfigurationResponse:
        self.logger.debug("Responding to workspace configuration request")
        # Return empty configuration values for all requested items
        # In a real implementation, this would fetch actual configuration values
        return types.ConfigurationResponse(
            id=req.id,
            result=[],
        )
