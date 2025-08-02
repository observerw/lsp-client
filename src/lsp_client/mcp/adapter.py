from __future__ import annotations

from collections.abc import Callable, Sequence

from mcp.server.fastmcp import FastMCP

from lsp_client import LSPCapabilityClientBase, lsp_cap, lsp_type
from lsp_client.capability.protocol import LSPCapabilityProtocol

from .locate import Locate, locate_by_context, locate_by_lineno, nth_occurrence


def resolve_locate(
    client: LSPCapabilityClientBase,
    locate: Locate,
) -> lsp_type.Position:
    file_path = client.resolve_file_path(locate.relative_file_path)
    if locate.lineno:
        line_content = locate_by_lineno(file_path, locate.lineno)
        line = locate.lineno
    elif locate.context:
        result = locate_by_context(
            file_path, locate.context, offset=locate.offset_to_context
        )
        line = result.lineno
        line_content = result.content
    else:
        raise ValueError("Either 'lineno' or 'context' must be provided")

    character = nth_occurrence(line_content, locate.symbol, locate.occurrence)

    return lsp_type.Position(line, character)


type CapabilityAdapter = Callable[[LSPCapabilityClientBase], Callable]


def adapt_request_references(client: LSPCapabilityClientBase):
    async def request_references(locate: Locate) -> Sequence[lsp_type.Location] | None:
        assert isinstance(client, lsp_cap.WithRequestReferences)
        return await client.request_references(
            locate.relative_file_path,
            position=resolve_locate(client, locate),
        )

    return request_references


adapters: dict[LSPCapabilityProtocol, CapabilityAdapter] = {
    lsp_cap.WithRequestReferences: adapt_request_references,
}


class Adapter:
    client: LSPCapabilityClientBase
    server: FastMCP

    def register(self):
        raise NotImplementedError
