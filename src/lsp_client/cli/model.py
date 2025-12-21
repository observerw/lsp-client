from __future__ import annotations

from enum import Enum
from pathlib import Path

from lsprotocol import types as lsp_type
from pydantic import BaseModel, Field
from rich.console import Console, ConsoleOptions, RenderResult
from rich.markdown import Markdown

from lsp_client.utils.uri import from_local_uri


class CLIOutput(BaseModel):
    """Base class for CLI output models."""

    def to_markdown(self) -> str:
        """Convert the model to a markdown string."""
        raise NotImplementedError

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Rich render method."""
        yield Markdown(self.to_markdown())


class CLILocation(CLIOutput):
    """
    Represents a specific location in a source file.
    Normalized from lsp_type.Location and lsp_type.LocationLink.
    """

    path: str = Field(..., description="Absolute path to the file")
    line: int = Field(..., description="Start line number (0-indexed)")
    character: int = Field(..., description="Start character position (0-indexed)")
    end_line: int = Field(..., description="End line number")
    end_character: int = Field(..., description="End character position")
    snippet: str | None = Field(None, description="Code snippet at the location")

    @classmethod
    def from_lsp(
        cls,
        location: lsp_type.Location | lsp_type.LocationLink,
        read_snippet: bool = True,
    ) -> CLILocation:
        if isinstance(location, lsp_type.Location):
            uri = location.uri
            range_ = location.range
        elif isinstance(location, lsp_type.LocationLink):
            uri = location.target_uri
            range_ = location.target_selection_range
        else:
            raise ValueError(f"Unsupported location type: {type(location)}")

        path = str(from_local_uri(uri))

        snippet = None
        if read_snippet:
            try:
                p = Path(path)
                if p.exists() and p.is_file():
                    with open(p, encoding="utf-8", errors="replace") as f:
                        for i, file_line in enumerate(f):
                            if i == range_.start.line:
                                snippet = file_line.strip()
                                break
            except Exception:
                pass

        return cls(
            path=path,
            line=range_.start.line,
            character=range_.start.character,
            end_line=range_.end.line,
            end_character=range_.end.character,
            snippet=snippet,
        )

    def to_markdown(self) -> str:
        md = f"**{self.path}:{self.line}:{self.character}**"
        if self.snippet:
            ext = Path(self.path).suffix.lstrip(".")
            md += f"\n\n```{ext}\n{self.snippet}\n```"
        return md

    def __str__(self) -> str:
        base = f"{self.path}:{self.line}:{self.character}"
        if self.snippet:
            return f"{base}\n    {self.snippet}"
        return base


class CLIHover(CLIOutput):
    """
    Represents hover information.
    """

    contents: str = Field(..., description="The content of the hover")
    range_str: str | None = Field(None, description="Text representation of the range")

    @classmethod
    def from_lsp(cls, hover: lsp_type.Hover) -> CLIHover:
        contents = ""
        raw = hover.contents
        if isinstance(raw, lsp_type.MarkupContent):
            contents = raw.value
        elif isinstance(raw, str):
            contents = raw
        elif isinstance(raw, list):
            parts = []
            for item in raw:
                if isinstance(item, str):
                    parts.append(item)
                elif hasattr(item, "value"):
                    parts.append(str(item.value))
            contents = "\n\n".join(parts)
        elif hasattr(raw, "value"):
            contents = str(raw.value)

        range_str = None
        if hover.range:
            range_str = f"{hover.range.start.line}:{hover.range.start.character}-{hover.range.end.line}:{hover.range.end.character}"

        return cls(contents=contents, range_str=range_str)

    def to_markdown(self) -> str:
        res = self.contents
        if self.range_str:
            res = f"> {self.range_str}\n\n{res}"
        return res

    def __str__(self) -> str:
        res = self.contents
        if self.range_str:
            res = f"[{self.range_str}]\n{res}"
        return res


class CLISymbolKind(str, Enum):
    """String mapping for lsp_type.SymbolKind"""

    File = "File"
    Module = "Module"
    Namespace = "Namespace"
    Package = "Package"
    Class = "Class"
    Method = "Method"
    Property = "Property"
    Field = "Field"
    Constructor = "Constructor"
    Enum = "Enum"
    Interface = "Interface"
    Function = "Function"
    Variable = "Variable"
    Constant = "Constant"
    String = "String"
    Number = "Number"
    Boolean = "Boolean"
    Array = "Array"
    Object = "Object"
    Key = "Key"
    Null = "Null"
    EnumMember = "EnumMember"
    Struct = "Struct"
    Event = "Event"
    Operator = "Operator"
    TypeParameter = "TypeParameter"
    Unknown = "Unknown"

    @classmethod
    def from_lsp(cls, kind: lsp_type.SymbolKind) -> str:
        try:
            return cls(kind.name).value
        except (ValueError, AttributeError):
            mapping = {
                1: "File",
                2: "Module",
                3: "Namespace",
                4: "Package",
                5: "Class",
                6: "Method",
                7: "Property",
                8: "Field",
                9: "Constructor",
                10: "Enum",
                11: "Interface",
                12: "Function",
                13: "Variable",
                14: "Constant",
                15: "String",
                16: "Number",
                17: "Boolean",
                18: "Array",
                19: "Object",
                20: "Key",
                21: "Null",
                22: "EnumMember",
                23: "Struct",
                24: "Event",
                25: "Operator",
                26: "TypeParameter",
            }
            return mapping.get(int(kind), "Unknown")


class CLISymbol(CLIOutput):
    """
    Represents a symbol (document or workspace).
    Normalized from lsp_type.DocumentSymbol and lsp_type.SymbolInformation.
    """

    name: str
    kind: str
    location: CLILocation | None = Field(default=None)
    container_name: str | None = None
    children: list[CLISymbol] = Field(default_factory=list)

    @classmethod
    def from_lsp(
        cls,
        symbol: lsp_type.DocumentSymbol | lsp_type.SymbolInformation,
        uri: str | None = None,
    ) -> CLISymbol:
        if isinstance(symbol, lsp_type.DocumentSymbol):
            loc = None
            if uri:
                loc_obj = lsp_type.Location(uri=uri, range=symbol.selection_range)
                loc = CLILocation.from_lsp(loc_obj)

            children = []
            if symbol.children:
                children = [cls.from_lsp(child, uri) for child in symbol.children]

            return cls(
                name=symbol.name,
                kind=CLISymbolKind.from_lsp(symbol.kind),
                location=loc,
                children=children,
            )

        elif isinstance(symbol, lsp_type.SymbolInformation):
            return cls(
                name=symbol.name,
                kind=CLISymbolKind.from_lsp(symbol.kind),
                location=CLILocation.from_lsp(symbol.location, read_snippet=False),
                container_name=symbol.container_name,
            )
        else:
            raise ValueError(f"Unsupported symbol type: {type(symbol)}")

    def to_markdown(self) -> str:
        loc_str = self.location.to_markdown() if self.location else ""
        md = f"### {self.kind}: `{self.name}`\n"
        if self.container_name:
            md += f"*(in {self.container_name})*\n"
        if loc_str:
            md += f"\n{loc_str}\n"

        if self.children:
            md += "\n#### Children\n"
            for child in self.children:
                child_md = child.to_markdown()
                md += "\n" + "\n".join(f"  {line}" for line in child_md.split("\n"))
        return md

    def __str__(self) -> str:
        loc_str = str(self.location) if self.location else ""
        if "\n" in loc_str:
            loc_lines = loc_str.split("\n")
            loc_str = loc_lines[0] + "\n    " + "\n    ".join(loc_lines[1:])

        return f"{self.kind} {self.name} {loc_str}".strip()


class CLITextEdit(CLIOutput):
    """
    Represents a text edit.
    """

    range: str = Field(..., description="Text representation of the range")
    new_text: str = Field(..., description="The new text")

    @classmethod
    def from_lsp(
        cls,
        edit: lsp_type.TextEdit | lsp_type.AnnotatedTextEdit | lsp_type.SnippetTextEdit,
    ) -> CLITextEdit:
        r = edit.range
        range_str = f"{r.start.line}:{r.start.character}-{r.end.line}:{r.end.character}"
        new_text = str(getattr(edit, "new_text", getattr(edit, "snippet", "")))
        return cls(range=range_str, new_text=new_text)

    def to_markdown(self) -> str:
        return f"- `[{self.range}]` -> `{self.new_text!r}`"


class CLIFileEdit(CLIOutput):
    """
    Represents edits in a single file.
    """

    path: str
    edits: list[CLITextEdit]

    def to_markdown(self) -> str:
        edits_md = "\n".join(e.to_markdown() for e in self.edits)
        return f"#### {self.path}\n{edits_md}"


class CLIWorkspaceEdit(CLIOutput):
    """
    Represents a workspace edit (e.g. from rename).
    """

    file_edits: list[CLIFileEdit] = Field(default_factory=list)

    @classmethod
    def from_lsp(cls, edit: lsp_type.WorkspaceEdit) -> CLIWorkspaceEdit:
        file_edits = []
        if edit.changes:
            for uri, edits in edit.changes.items():
                path = str(from_local_uri(uri))
                cli_edits = [CLITextEdit.from_lsp(e) for e in edits]
                file_edits.append(CLIFileEdit(path=path, edits=cli_edits))

        if edit.document_changes:
            for dc in edit.document_changes:
                if isinstance(dc, lsp_type.TextDocumentEdit):
                    path = str(from_local_uri(dc.text_document.uri))
                    cli_edits = [CLITextEdit.from_lsp(e) for e in dc.edits]
                    file_edits.append(CLIFileEdit(path=path, edits=cli_edits))

        return cls(file_edits=file_edits)

    def to_markdown(self) -> str:
        if not self.file_edits:
            return "_No changes._"
        return "## Workspace Edits\n\n" + "\n\n".join(
            fe.to_markdown() for fe in self.file_edits
        )

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Markdown(self.to_markdown())

    def __str__(self) -> str:
        if not self.file_edits:
            return "No changes."
        res = []
        for fe in self.file_edits:
            res.append(f"File: {fe.path}")
            for e in fe.edits:
                res.append(f"  [{e.range}] -> {e.new_text!r}")
        return "\n".join(res)
