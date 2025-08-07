"""
pyrefly: Type checker and language server for Python - https://pyrefly.org/
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, final, override

from loguru import logger
from semver import Version

from lsp_client import lsp_cap, lsp_type
from lsp_client.client.stdio import StdioClient
from lsp_client.server.stdio import StdioServer


@final
@dataclass(kw_only=True)
class PyReflyServer(StdioServer):
    num_threads: int = 0

    @property
    @override
    def server_cmd(self) -> Sequence[str]:
        threads = (
            (
                "-j",
                f"{self.num_threads}",
            )
            if self.num_threads > 0
            else ()
        )

        return (
            "pyrefly",
            "lsp",
            *threads,
        )


@final
@dataclass(kw_only=True)
class PyReflyClient(
    lsp_cap.WithRequestReferences,
    lsp_cap.WithRequestDocumentSymbols,
    lsp_cap.WithRequestWorkspaceSymbolInformation,
    lsp_cap.WithRequestHover,
    lsp_cap.WithRequestSignatureHelp,
    lsp_cap.WithRequestCompletions,
    lsp_cap.WithReceiveLogMessage,
    lsp_cap.WithReceiveShowMessage,
    lsp_cap.WithReceiveLogTrace,
    StdioClient,
):
    """
    Keep track of <https://github.com/facebook/pyrefly/issues/344> for LSP features support.
    """

    server_threads: int = 0

    @property
    @override
    def language_id(self) -> lsp_type.LanguageKind:
        return lsp_type.LanguageKind.Python

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None):
        # TODO for now, pyrefly does not provide server info
        if not info:
            return

        version = info.version
        assert version, "Server version is required for compatibility check"

        assert Version.parse(version).match(">=0.24.0")
        logger.debug(
            "Server version {} supports PyReflyClient capabilities",
            version,
        )

    @override
    def create_initialization_options(self) -> dict[str, Any] | None:
        return

    @override
    def create_server(self) -> PyReflyServer:
        return PyReflyServer(
            process_count=self.server_count,
            info=self.server_info,
            num_threads=self.server_threads,
        )
