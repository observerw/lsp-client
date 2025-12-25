from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol, override, runtime_checkable

from loguru import logger

from lsp_client.protocol import (
    CapabilityClientProtocol,
    ServerRequestHook,
    ServerRequestHookProtocol,
    ServerRequestHookRegistry,
    WorkspaceCapabilityProtocol,
)
from lsp_client.utils.types import lsp_type


@runtime_checkable
class WithRespondWorkspaceFoldersRequest(
    WorkspaceCapabilityProtocol,
    ServerRequestHookProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `workspace/workspaceFolders` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_workspaceFolders
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (lsp_type.WORKSPACE_WORKSPACE_FOLDERS,)

    @override
    @classmethod
    def register_workspace_capability(
        cls, cap: lsp_type.WorkspaceClientCapabilities
    ) -> None:
        super().register_workspace_capability(cap)
        cap.workspace_folders = True

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)

    async def _respond_workspace_folders(
        self, params: None
    ) -> Sequence[lsp_type.WorkspaceFolder] | None:
        logger.debug("Responding to workspace folders request")
        return self.get_workspace().to_folders()

    async def respond_workspace_folders_request(
        self, req: lsp_type.WorkspaceFoldersRequest
    ) -> lsp_type.WorkspaceFoldersResponse:
        return lsp_type.WorkspaceFoldersResponse(
            id=req.id,
            result=await self._respond_workspace_folders(req.params),
        )

    @override
    def register_server_request_hooks(
        self, registry: ServerRequestHookRegistry
    ) -> None:
        super().register_server_request_hooks(registry)
        registry.register(
            lsp_type.WORKSPACE_WORKSPACE_FOLDERS,
            ServerRequestHook(
                cls=lsp_type.WorkspaceFoldersRequest,
                execute=self.respond_workspace_folders_request,
            ),
        )
