"""
basedpyright: Language Server for Python - https://docs.basedpyright.com
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from typing import override

from semver import Version

from lsp_client import (
    BaseLSPCapabilityClientArgs,
    FullFeaturedCapabilityGroup,
    LSPCapabilityClientBase,
    LSPClientBase,
    WorkspaceFolder,
    lsp_type,
)
from lsp_client.server import LSPServerPool

logger = logging.getLogger(__name__)


class BasedPyrightCapabilityClient(
    FullFeaturedCapabilityGroup,
    LSPCapabilityClientBase,
):
    @property
    @override
    def language_id(self) -> lsp_type.LanguageKind:
        return lsp_type.LanguageKind.Python

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None):
        assert info, "Server info must be provided to check compatibility"

        version = info.version
        assert version, "Server version is required for compatibility check"

        assert Version.parse(version).match(">=1.29.0")
        logger.debug(
            "Server version %s supports BasedPyrightClient capabilities",
            version,
        )


class BasedPyrightClient(LSPClientBase[BasedPyrightCapabilityClient]):
    @property
    @override
    def server_cmd(self) -> Sequence[str]:
        return (
            "basedpyright-langserver",
            "--stdio",
        )

    @override
    @asynccontextmanager
    async def _start_client(
        self,
        server: LSPServerPool,
        workspace: Sequence[WorkspaceFolder],
    ) -> AsyncGenerator[BasedPyrightCapabilityClient]:
        async with BasedPyrightCapabilityClient.start(
            server=server,
            args=BaseLSPCapabilityClientArgs(
                workspace_folders=workspace,
                initialization_options={},
                sync_file=self.sync_file,
            ),
        ) as client:
            yield client
