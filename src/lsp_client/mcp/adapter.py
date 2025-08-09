from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Literal

from lsprotocol.types import Position
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from lsp_client import lsp_cap, lsp_type
from lsp_client.capability.protocol import LSPCapabilityProtocol
from lsp_client.mcp.protocol import MCPClientProtocol
from lsp_client.utils.path import AbsPath


def resolve_line(text: str, pattern: str) -> int:
    line: int | None = None

    for i, content in enumerate(text.splitlines()):
        if pattern not in content:
            continue

        if line is not None:
            raise ValueError(f"Pattern {pattern} found in multiple lines")

        line = i

    if line is None:
        raise ValueError(f"Pattern {pattern} not found in text")

    return line


type CharacterIndicator = Literal["·"]


def resolve_character(
    text: str,
    pattern: str,
    *,
    indicator: CharacterIndicator | None = None,
) -> int:
    sub_idx = text.index(pattern)

    if indicator:
        indicator_idx = pattern.index(indicator)
        return sub_idx + indicator_idx - 1

    return sub_idx


def resolve_position(
    text: str, pattern: str, *, indicator: CharacterIndicator | None = None
) -> lsp_type.Position:
    line = resolve_line(text, pattern.replace(indicator, "") if indicator else pattern)
    character = resolve_character(text, pattern, indicator=indicator)

    return lsp_type.Position(line, character)


def read_line_range(file_path: AbsPath, line_range: tuple[int, int]) -> str:
    lines: list[str] = []

    with file_path.open("r") as f:
        for i, line in enumerate(f):
            if i < line_range[0]:
                continue
            if i >= line_range[1]:
                break
            lines.append(line)

    return "\n".join(lines)


class Locate(BaseModel):
    relative_file_path: str = Field(
        description="Relative path to the file containing the symbol. "
    )

    pattern: str = Field(
        description="Location pattern to locate the symbol in the file. You may "
        "use `indicator` to locate the character in the line."
        "If not provided, the first occurrence of the pattern will be used."
    )

    indicator: CharacterIndicator | None = Field(
        default=None,
        description="If provided in `pattern`, "
        "it will be used to locate the character in the line.",
    )

    line_range: tuple[int, int] | None = Field(
        default=None,
        description="If provided, the position will be resolved in the line range. "
        "The line range is inclusive. "
        "If not provided, the position will be resolved in the entire file.",
    )

    def resolve(self, client: MCPClientProtocol) -> Position:
        file_path = client.resolve_path(self.relative_file_path)
        offset = self.line_range[0] if self.line_range else 0

        text = (
            read_line_range(file_path, self.line_range)
            if self.line_range
            else file_path.read_text()
        )

        position = resolve_position(text, self.pattern, indicator=self.indicator)
        position.line += offset

        return position


def adapt_request_references(client: MCPClientProtocol):
    async def request_references(locate: Locate) -> Sequence[lsp_type.Location] | None:
        assert isinstance(client, lsp_cap.WithRequestReferences)
        return await client.request_references(
            locate.relative_file_path,
            position=locate.resolve(client),
        )

    return request_references


def adapter_requets_definition(client: MCPClientProtocol):
    async def request_definition(locate: Locate) -> Sequence[lsp_type.Location] | None:
        assert isinstance(client, lsp_cap.WithRequestDefinition)
        match await client.request_definition(
            locate.relative_file_path,
            position=locate.resolve(client),
        ):
            case None:
                return None
            case locations if client.is_locations(locations):
                return locations
            # HACK for definition links, we just simplify it to locations
            case links if client.is_definition_links(links):
                return [
                    lsp_type.Location(uri=link.target_uri, range=link.target_range)
                    for link in links
                ]

    return request_definition


type CapabilityAdapter = Callable[[MCPClientProtocol], Callable]
adapters: dict[LSPCapabilityProtocol, CapabilityAdapter] = {
    lsp_cap.WithRequestReferences: adapt_request_references,
    lsp_cap.WithRequestDefinition: adapter_requets_definition,
}


def register_adapters(client: MCPClientProtocol, server: FastMCP):
    for cap, adapter in adapters.items():
        if not isinstance(client, cap):  # type: ignore LSPCapabilityProtocol is runtime checkable
            continue

        server.add_tool(adapter(client))
