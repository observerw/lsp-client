from __future__ import annotations

import linecache
from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field, model_validator

from lsp_client import Position


def locate_by_context(file_path: Path, context: str) -> tuple[int, str]:
    """Return the first line content that contains the context."""

    with open(file_path, encoding="utf-8") as file:
        for lineno, line in enumerate(file, start=1):
            if context not in line:
                continue

            return lineno, line

    raise ValueError(f"Context '{context}' not found in file '{file_path}'")


def locate_by_lineno(file_path: Path, lineno: int) -> str:
    """Return the content of the line at the given line number."""
    return linecache.getline(file_path.as_posix(), lineno)


class Locate(BaseModel):
    """Locate a symbol in a code file."""

    rel_file_path: Path = Field(
        description="Relative path to the file containing the symbol. "
    )

    symbol: str = Field(
        description="The symbol you are interested in.",
    )

    lineno: int | None = Field(
        None,
        description="Line number of the symbol in the file. If provided, will look for the first occurrence of the symbol on that line.",
    )

    context: str | None = Field(
        None,
        description="Context around the symbol. If provided, will look through the whole file to find the context, then locate the first occurrence of the symbol in that context.",
    )

    @model_validator(mode="after")
    def _validate(self) -> Self:
        if not (self.lineno or self.context):
            raise ValueError("Either 'lineno' or 'context' must be provided")

        return self

    def resolve(self, repo_path: Path) -> Position:
        """Resolve the relative file path to an absolute position."""

        abs_file_path = repo_path / self.rel_file_path

        if self.lineno:
            line_content = locate_by_lineno(abs_file_path, self.lineno)
            line = self.lineno
        elif self.context:
            line, line_content = locate_by_context(abs_file_path, self.context)
        else:
            raise ValueError("Either 'lineno' or 'context' must be provided")

        character = line_content.find(self.symbol)

        return Position(line, character)
