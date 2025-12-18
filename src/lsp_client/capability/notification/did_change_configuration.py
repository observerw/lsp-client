from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, override, runtime_checkable

from lsp_client.protocol import CapabilityClientProtocol, WorkspaceCapabilityProtocol
from lsp_client.utils.types import lsp_type


@runtime_checkable
class WithNotifyDidChangeConfiguration(
    WorkspaceCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `workspace/didChangeConfiguration` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_didChangeConfiguration
    """

    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (lsp_type.WORKSPACE_DID_CHANGE_CONFIGURATION,)

    @override
    @classmethod
    def register_workspace_capability(
        cls, cap: lsp_type.WorkspaceClientCapabilities
    ) -> None:
        cap.did_change_configuration = (
            lsp_type.DidChangeConfigurationClientCapabilities()
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        cap: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ) -> None:
        super().check_server_capability(cap, info)
        return

    async def notify_change_configuration(self, settings: Any | None) -> None:
        return await self.notify(
            lsp_type.DidChangeConfigurationNotification(
                params=lsp_type.DidChangeConfigurationParams(settings=settings)
            ),
        )
