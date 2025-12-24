from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, override, runtime_checkable

from lsp_client.protocol import (
    CapabilityClientProtocol,
    ServerRequestHook,
    ServerRequestHookProtocol,
    ServerRequestHookRegistry,
    WorkspaceCapabilityProtocol,
)
from lsp_client.utils.types import lsp_type


@runtime_checkable
class WithRespondInlayHintRefresh(
    WorkspaceCapabilityProtocol,
    ServerRequestHookProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `workspace/inlayHint/refresh` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_inlayHint_refresh
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (lsp_type.WORKSPACE_INLAY_HINT_REFRESH,)

    @override
    @classmethod
    def register_workspace_capability(
        cls, cap: lsp_type.WorkspaceClientCapabilities
    ) -> None:
        super().register_workspace_capability(cap)
        cap.inlay_hint = lsp_type.InlayHintWorkspaceClientCapabilities(
            refresh_support=True
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)

    async def _respond_inlay_hint_refresh(self, params: None) -> None:
        return None

    async def respond_inlay_hint_refresh(
        self, req: lsp_type.InlayHintRefreshRequest
    ) -> lsp_type.InlayHintRefreshResponse:
        return lsp_type.InlayHintRefreshResponse(
            id=req.id,
            result=await self._respond_inlay_hint_refresh(req.params),
        )

    @override
    def register_server_request_hooks(
        self, registry: ServerRequestHookRegistry
    ) -> None:
        super().register_server_request_hooks(registry)
        registry.register(
            lsp_type.WORKSPACE_INLAY_HINT_REFRESH,
            ServerRequestHook(
                cls=lsp_type.InlayHintRefreshRequest,
                execute=self.respond_inlay_hint_refresh,
            ),
        )
