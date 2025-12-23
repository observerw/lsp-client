from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import CapabilityClientProtocol, TextDocumentCapabilityProtocol
from lsp_client.utils.types import AnyPath, Range, lsp_type


@runtime_checkable
class WithRequestInlineValue(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/inlineValue` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_inlineValue
    """

    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (lsp_type.TEXT_DOCUMENT_INLINE_VALUE,)

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        cap.inline_value = lsp_type.InlineValueClientCapabilities(
            dynamic_registration=True
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.inline_value_provider

    async def request_inline_value(
        self,
        file_path: AnyPath,
        range: Range,
        context: lsp_type.InlineValueContext,
    ) -> Sequence[lsp_type.InlineValue] | None:
        """
        Request inline values for the given range in the text document.

        Args:
            file_path: Path to the text document
            range: Range for which inline values are requested
            context: Debug session context information

        Returns:
            List of inline value objects containing the computed inline values
        """
        return await self.file_request(
            lsp_type.InlineValueRequest(
                id=jsonrpc_uuid(),
                params=lsp_type.InlineValueParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    range=range,
                    context=context,
                ),
            ),
            schema=lsp_type.InlineValueResponse,
            file_paths=[file_path],
        )
