from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import CapabilityClientProtocol, TextDocumentCapabilityProtocol
from lsp_client.utils.types import AnyPath, Position, lsp_type


@runtime_checkable
class WithRequestReferences(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/references` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_references
    """

    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (lsp_type.TEXT_DOCUMENT_REFERENCES,)

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        cap.references = lsp_type.ReferenceClientCapabilities()

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.references_provider

    async def request_references(
        self,
        file_path: AnyPath,
        position: Position,
        *,
        include_declaration: bool = True,
    ) -> Sequence[lsp_type.Location] | None:
        return await self.file_request(
            lsp_type.ReferencesRequest(
                id=jsonrpc_uuid(),
                params=lsp_type.ReferenceParams(
                    context=lsp_type.ReferenceContext(
                        include_declaration=include_declaration
                    ),
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                ),
            ),
            schema=lsp_type.ReferencesResponse,
            file_paths=[file_path],
        )
