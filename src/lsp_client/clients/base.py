from __future__ import annotations

from abc import ABC
from pathlib import Path
from typing import override

from lsp_client.client.abc import Client
from lsp_client.client.lang import LanguageConfig
from lsp_client.utils.types import lsp_type


class PythonClientBase(Client, ABC):
    @classmethod
    def check_project_root(cls, path: Path) -> bool:
        return any(
            (path / f).exists()
            for f in (
                "pyproject.toml",
                "setup.py",
                "setup.cfg",
                "requirements.txt",
                ".python-version",
            )
        )

    @override
    def get_language_config(self) -> LanguageConfig:
        return LanguageConfig(
            kind=lsp_type.LanguageKind.Python,
            suffixes=[".py", ".pyi"],
            project_files=[
                "pyproject.toml",
                "setup.py",
                "setup.cfg",
                "requirements.txt",
                ".python-version",
            ],
        )


class RustClientBase(Client, ABC):
    @classmethod
    def check_project_root(cls, path: Path) -> bool:
        return (path / "Cargo.toml").exists()

    @override
    def get_language_config(self) -> LanguageConfig:
        return LanguageConfig(
            kind=lsp_type.LanguageKind.Rust,
            suffixes=[".rs"],
            project_files=["Cargo.toml"],
        )


class GoClientBase(Client, ABC):
    @classmethod
    def check_project_root(cls, path: Path) -> bool:
        return (path / "go.mod").exists()

    @override
    def get_language_config(self) -> LanguageConfig:
        return LanguageConfig(
            kind=lsp_type.LanguageKind.Go,
            suffixes=[".go"],
            project_files=["go.mod"],
        )


class TypeScriptClientBase(Client, ABC):
    @classmethod
    def check_project_root(cls, path: Path) -> bool:
        return any(
            (path / f).exists()
            for f in ("package.json", "tsconfig.json", "jsconfig.json")
        )

    @override
    def get_language_config(self) -> LanguageConfig:
        return LanguageConfig(
            kind=lsp_type.LanguageKind.TypeScript,
            suffixes=[".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"],
            project_files=["package.json", "tsconfig.json", "jsconfig.json"],
        )
