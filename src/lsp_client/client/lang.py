from __future__ import annotations

from pathlib import Path

from attrs import Factory, frozen

from lsp_client.utils.workspace import lsp_type


@frozen
class LanguageConfig:
    """Configuration for a programming language in the LSP client."""

    kind: lsp_type.LanguageKind
    """The kind of programming language."""

    suffixes: list[str]
    """File suffixes associated with the language."""

    project_files: list[str]
    """Files that indicate the root of a project for this language."""

    exclude_files: list[str] = Factory(list)
    """Files that indicate a directory should not be considered a project root for this language."""

    def find_project_root(self, file_path: Path) -> Path | None:
        """Find the project root directory for the given file path.

        Args:
            file_path (Path): The file path to check.
        Returns:
            Path | None: The project root directory if found, otherwise None.
        """

        if not file_path.is_file():
            raise ValueError(f"Expected a file path, got: {file_path}")

        if not any(file_path.name.endswith(suffix) for suffix in self.suffixes):
            return

        for parent in file_path.parents:
            if any((parent / excl).exists() for excl in self.exclude_files):
                return
            if any((parent / proj).exists() for proj in self.project_files):
                return parent

        return file_path.parent
