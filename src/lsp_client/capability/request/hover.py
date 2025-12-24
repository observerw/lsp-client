from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, override, runtime_checkable

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import CapabilityClientProtocol, TextDocumentCapabilityProtocol
from lsp_client.utils.types import AnyPath, Position, lsp_type


@runtime_checkable
class WithRequestHover(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/hover` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_hover
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (lsp_type.TEXT_DOCUMENT_HOVER,)

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        cap.hover = lsp_type.HoverClientCapabilities(
            content_format=[
                lsp_type.MarkupKind.Markdown,
                lsp_type.MarkupKind.PlainText,
            ]
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.hover_provider

    async def _request_hover(
        self, params: lsp_type.HoverParams
    ) -> lsp_type.HoverResult:
        return await self.request(
            lsp_type.HoverRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.HoverResponse,
        )

    async def request_hover(
        self, file_path: AnyPath, position: Position
    ) -> lsp_type.MarkupContent | None:
        async with self.open_files(file_path):
            hover = await self._request_hover(
                lsp_type.HoverParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                )
            )

        if hover is None:
            return None

        def to_block(item: object) -> str:
            match item:
                case lsp_type.MarkedStringWithLanguage(
                    language=str() as lang, value=str() as val
                ):
                    return f"```{lang}\n{val}\n```"
                case str() as s:
                    return f"```plaintext\n{s}\n```"
                case _:
                    return f"```plaintext\n{item!s}\n```"

        match contents := hover.contents:
            case lsp_type.MarkupContent() as mc:
                return mc
            case lsp_type.MarkedStringWithLanguage():
                return lsp_type.MarkupContent(
                    kind=lsp_type.MarkupKind.Markdown,
                    value=to_block(contents),
                )
            case str():
                return lsp_type.MarkupContent(
                    kind=lsp_type.MarkupKind.Markdown,
                    value=to_block(contents),
                )
            case list() as items:
                return lsp_type.MarkupContent(
                    kind=lsp_type.MarkupKind.Markdown,
                    value="\n\n".join(to_block(i) for i in items),
                )
            case tuple() as items:
                return lsp_type.MarkupContent(
                    kind=lsp_type.MarkupKind.Markdown,
                    value="\n\n".join(to_block(i) for i in items),
                )
            case _:
                return lsp_type.MarkupContent(
                    kind=lsp_type.MarkupKind.Markdown,
                    value=to_block(contents),
                )
