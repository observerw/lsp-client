"""
pyrefly: Type checker and language server for Python - https://pyrefly.org/
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import ClassVar, override

from semver import Version

from lsp_client import LSPClientBase, lsp_cap, lsp_type

logger = logging.getLogger(__name__)


class PyReflyClient(
    lsp_cap.WithRequestReferences,
    lsp_cap.WithRequestDocumentSymbols,
    lsp_cap.WithRequestHover,
    lsp_cap.WithRequestSignatureHelp,
    lsp_cap.WithRequestCompletions,
    lsp_cap.WithNotifyPublishDiagnostics,
    lsp_cap.WithReceiveLogMessage,
    lsp_cap.WithReceiveShowMessage,
    lsp_cap.WithReceiveLogTrace,
    LSPClientBase,
):
    """
    Keep track of <https://github.com/facebook/pyrefly/issues/344> for LSP features support.
    """

    language_id: ClassVar[lsp_type.LanguageKind] = lsp_type.LanguageKind.Python
    server_cmd: ClassVar[Sequence[str]] = (
        "pyrefly",
        "lsp",
        "-v",
    )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        if info and (version := info.version):
            assert Version.parse(version).match(">=0.24")

            logger.debug(
                "Server version %s supports PyReflyClient capabilities",
                version,
            )
