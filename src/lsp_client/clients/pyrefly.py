"""
pyrefly: Type checker and language server for Python - https://pyrefly.org/
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from semver import Version

from lsp_client import (
    BaseLSPCapabilityClientArgs,
    LSPCapabilityClientBase,
    LSPClientBase,
    WorkspaceFolder,
    lsp_cap,
    lsp_type,
)
from lsp_client.server import LSPServerPool

logger = logging.getLogger(__name__)


class PyReflyCapabilityClient(
    lsp_cap.WithRequestReferences,
    lsp_cap.WithRequestDocumentSymbols,
    lsp_cap.WithRequestHover,
    lsp_cap.WithRequestSignatureHelp,
    lsp_cap.WithRequestCompletions,
    lsp_cap.WithReceiveLogMessage,
    lsp_cap.WithReceiveShowMessage,
    lsp_cap.WithReceiveLogTrace,
    LSPCapabilityClientBase,
):
    """
    Keep track of <https://github.com/facebook/pyrefly/issues/344> for LSP features support.
    """

    @property
    @override
    def language_id(self) -> lsp_type.LanguageKind:
        return lsp_type.LanguageKind.Python

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None):
        # TODO for now, pyrefly does not provide server info.
        if not info:
            return

        version = info.version
        assert version, "Server version is required for compatibility check"

        assert Version.parse(version).match(">=0.24.0")
        logger.debug(
            "Server version %s supports BasedPyrightClient capabilities",
            version,
        )


@dataclass(frozen=True)
class PyReflyClient(LSPClientBase[PyReflyCapabilityClient]):
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

    @override
    @asynccontextmanager
    async def _start_client(
        self,
        server: LSPServerPool,
        workspace: Sequence[WorkspaceFolder],
    ) -> AsyncGenerator[PyReflyCapabilityClient]:
        async with PyReflyCapabilityClient.start(
            server=server,
            args=BaseLSPCapabilityClientArgs(
                workspace_folders=workspace,
                initialization_options={},
                sync_file=self.sync_file,
            ),
        ) as client:
            yield client
