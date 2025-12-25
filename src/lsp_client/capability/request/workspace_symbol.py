from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol, override, runtime_checkable

from loguru import logger

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import CapabilityClientProtocol, WorkspaceCapabilityProtocol
from lsp_client.utils.type_guard import is_symbol_information_seq, is_workspace_symbols
from lsp_client.utils.types import lsp_type
from lsp_client.utils.warn import deprecated


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
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (lsp_type.WORKSPACE_SYMBOL,)

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

    async def _request_workspace_symbol(
        self, params: lsp_type.WorkspaceSymbolParams
    ) -> lsp_type.WorkspaceSymbolResult:
        return await self.request(
            lsp_type.WorkspaceSymbolRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.WorkspaceSymbolResponse,
        )

    async def request_workspace_symbol(
        self, query: str
    ) -> (
        Sequence[lsp_type.SymbolInformation] | Sequence[lsp_type.WorkspaceSymbol] | None
    ):
        return await self._request_workspace_symbol(
            lsp_type.WorkspaceSymbolParams(query=query)
        )

    @deprecated("Use 'request_workspace_symbol_list' instead.")
    async def request_workspace_symbol_information_list(
        self, query: str
    ) -> Sequence[lsp_type.SymbolInformation] | None:
        match await self.request_workspace_symbol(query):
            case result if is_symbol_information_seq(result):
                return list(result)
            case other:
                logger.warning(
                    "Workspace symbol returned with unexpected result: {}", other
                )
                return None

    async def request_workspace_symbol_list(
        self, query: str
    ) -> Sequence[lsp_type.WorkspaceSymbol] | None:
        match await self.request_workspace_symbol(query):
            case result if is_workspace_symbols(result):
                return list(result)
            case other:
                logger.warning(
                    "Workspace symbol returned with unexpected result: {}", other
                )
                return None
