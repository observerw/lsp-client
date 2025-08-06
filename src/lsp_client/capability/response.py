"""
Server-side request/notification.
"""

from __future__ import annotations

from typing import Protocol, override, runtime_checkable

from loguru import logger

from lsp_client import lsp_type

from .protocol import LSPCapabilityClientProtocol, LSPCapabilityProtocol


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
    def client_capability(cls) -> lsp_type.ClientCapabilities:
        # logMessage don't need client capabilities
        return lsp_type.ClientCapabilities()

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        logger.debug("Server supports window/logMessage checked")

    async def receive_log_message(self, req: lsp_type.LogMessageNotification):
        logger.debug("Received log message: {}", req.params.message)


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
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        logger.debug("Server supports window/logTrace checked")

    async def receive_log_trace(self, req: lsp_type.LogTraceNotification):
        logger.debug("Received log trace: {}", req.params.message)


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
    def client_capability(cls) -> lsp_type.ClientCapabilities:
        return lsp_type.ClientCapabilities(
            window=lsp_type.WindowClientCapabilities(
                show_message=lsp_type.ShowMessageRequestClientCapabilities(
                    message_action_item=lsp_type.ClientShowMessageActionItemOptions(
                        additional_properties_support=True,
                    ),
                ),
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        logger.debug("Server supports window/showMessage checked")

    async def receive_show_message(self, req: lsp_type.ShowMessageNotification):
        logger.debug("Received show message: {}", req.params.message)


@runtime_checkable
class WithReceivePublishDiagnostics(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/publishDiagnostics` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_publishDiagnostics
    """

    @override
    @classmethod
    def client_capability(cls) -> lsp_type.ClientCapabilities:
        return lsp_type.ClientCapabilities(
            text_document=lsp_type.TextDocumentClientCapabilities(
                publish_diagnostics=lsp_type.PublishDiagnosticsClientCapabilities(
                    related_information=True,
                    version_support=True,
                    tag_support=lsp_type.ClientDiagnosticsTagOptions(
                        value_set=[lsp_type.DiagnosticTag.Deprecated]
                    ),
                    code_description_support=True,
                )
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        logger.debug("Server supports textDocument/publishDiagnostics checked")

    async def receive_publish_diagnostics(
        self, req: lsp_type.PublishDiagnosticsNotification
    ) -> None:
        # TODO add support for diagnostic handling
        logger.debug(
            "Received publish diagnostics for {}",
            req.params.uri,
        )


@runtime_checkable
class WithRespondShowMessageRequest(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    """
    `window/showMessageRequest` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#window_showMessageRequest
    """

    @override
    @classmethod
    def client_capability(cls) -> lsp_type.ClientCapabilities:
        return lsp_type.ClientCapabilities(
            window=lsp_type.WindowClientCapabilities(
                show_message=lsp_type.ShowMessageRequestClientCapabilities(
                    message_action_item=lsp_type.ClientShowMessageActionItemOptions(
                        additional_properties_support=True,
                    ),
                ),
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        logger.debug("Server supports window/showMessageRequest checked")

    async def respond_show_message(
        self, req: lsp_type.ShowMessageRequest
    ) -> lsp_type.ShowMessageResponse:
        logger.debug("Responding to show message: {}", req.params.message)
        return lsp_type.ShowMessageResponse(id=req.id)


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
    def client_capability(cls) -> lsp_type.ClientCapabilities:
        return lsp_type.ClientCapabilities(
            workspace=lsp_type.WorkspaceClientCapabilities(workspace_folders=True)
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        logger.debug("Server supports workspace/workspaceFolders checked")

    async def respond_workspace_folders(
        self, req: lsp_type.WorkspaceFoldersRequest
    ) -> lsp_type.WorkspaceFoldersResponse:
        logger.debug("Responding to workspace folders request")
        return lsp_type.WorkspaceFoldersResponse(
            id=req.id,
            result=self.workspace_folders,
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
    def client_capability(cls) -> lsp_type.ClientCapabilities:
        return lsp_type.ClientCapabilities(
            workspace=lsp_type.WorkspaceClientCapabilities(
                configuration=True,
                workspace_folders=True,
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        logger.debug("Server supports workspace/configuration checked")

    async def respond_workspace_configuration(
        self, req: lsp_type.ConfigurationRequest
    ) -> lsp_type.ConfigurationResponse:
        logger.debug("Responding to workspace configuration request")
        # Return empty configuration values for all requested items
        # In a real implementation, this would fetch actual configuration values
        return lsp_type.ConfigurationResponse(
            id=req.id,
            result=[],
        )
