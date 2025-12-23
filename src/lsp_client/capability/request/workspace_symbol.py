from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import CapabilityClientProtocol, WorkspaceCapabilityProtocol
from lsp_client.utils.types import lsp_type


@runtime_checkable
class WithRequestWorkspaceSymbol(
    WorkspaceCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `workspace/symbol` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_symbol
    """

    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (lsp_type.WORKSPACE_SYMBOL,)

    @override
    @classmethod
    def register_workspace_capability(
        cls, cap: lsp_type.WorkspaceClientCapabilities
    ) -> None:
        cap.symbol = lsp_type.WorkspaceSymbolClientCapabilities(
            symbol_kind=lsp_type.ClientSymbolKindOptions(
                value_set=[*lsp_type.SymbolKind]
            ),
            tag_support=lsp_type.ClientSymbolTagOptions(
                value_set=[*lsp_type.SymbolTag],
            ),
            resolve_support=lsp_type.ClientSymbolResolveOptions(
                properties=["location.range", "location.uri"]
            ),
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.workspace_symbol_provider

    async def request_workspace_symbol(
        self, query: str
    ) -> (
        Sequence[lsp_type.SymbolInformation] | Sequence[lsp_type.WorkspaceSymbol] | None
    ):
        return await self.request(
            lsp_type.WorkspaceSymbolRequest(
                id=jsonrpc_uuid(),
                params=lsp_type.WorkspaceSymbolParams(query=query),
            ),
            schema=lsp_type.WorkspaceSymbolResponse,
        )
