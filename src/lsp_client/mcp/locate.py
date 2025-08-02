from __future__ import annotations

import linecache
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field, model_validator

from lsp_client import Position


def nth_occurrence(s: str, sub: str, n: int) -> int:
    index: int = -1

    for _ in range(n):
        if (index := s.find(sub, index + 1)) == -1:
            raise ValueError(f"'{sub}' not found {n} times in the string.")

    return index


@dataclass
class LocateResult:
    lineno: int
    content: str


def locate_by_context(
    file_path: Path, context: str, *, offset: int = 0
) -> LocateResult:
    """Return the line content that contains the context, with optional offset."""

    window: deque[LocateResult] = deque(maxlen=offset + 1)

    with open(file_path, encoding="utf-8") as file:
        target_lineno: int | None = None

        for lineno, line in enumerate(file, start=1):
            if target_lineno and lineno == target_lineno:
                return LocateResult(lineno=lineno, content=line)

            if context not in line:
                window.append(LocateResult(lineno=lineno, content=line))
                continue

            if offset > 0:
                target_lineno = lineno + offset
                continue

            if abs(offset) > len(window):
                raise ValueError(
                    f"Offset {offset} is larger than the number of lines in the file."
                )

            return window[offset]

    raise ValueError(f"Context '{context}' not found in file {file_path}")


def locate_by_lineno(file_path: Path, lineno: int) -> str:
    """Return the content of the line at the given line number."""
    return linecache.getline(file_path.as_posix(), lineno)


class Locate(BaseModel):
    """Locate a symbol in a code file."""

    relative_file_path: Path = Field(
        description="Relative path to the file containing the symbol. "
    )

    symbol: str = Field(
        description="The symbol you are interested in.",
    )

    occurrence: int = 1
    """The occurrence of the symbol to locate. Defaults to 1, meaning the first occurrence."""

    lineno: int | None = Field(
        None,
        description="Line number of the symbol in the file. If provided, will look for the `occurrence` of the symbol on that line.",
    )

    context: str | None = Field(
        None,
        description="Context around the symbol. If provided, will look through the whole file to find the context, then locate the `occurrence` of the symbol in that context.",
    )

    offset_to_context: int = 0
    """When using `context`, this is the offset from the line of the context to the line that contains the symbol. Defaults to 0, meaning the symbol is on the same line as the context."""

    @model_validator(mode="after")
    def _validate(self) -> Self:
        if not (self.lineno or self.context):
            raise ValueError("Either 'lineno' or 'context' must be provided")

        return self

    def resolve(self, repo_path: Path) -> Position:
        """Resolve the relative file path to an absolute position."""

        abs_file_path = repo_path / self.relative_file_path

        if self.lineno:
            line_content = locate_by_lineno(abs_file_path, self.lineno)
            line = self.lineno
        elif self.context:
            result = locate_by_context(
                abs_file_path, self.context, offset=self.offset_to_context
            )
            line = result.lineno
            line_content = result.content
        else:
            raise ValueError("Either 'lineno' or 'context' must be provided")

        character = nth_occurrence(line_content, self.symbol, self.occurrence)

        return Position(line, character)
