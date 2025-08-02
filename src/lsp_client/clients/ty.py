"""
ty: Type checker and language server for Python - https://docs.astral.sh/ty/
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Literal, final, override

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


@final
@dataclass
class TyCapabilityClient(
    lsp_cap.WithRequestReferences,
    lsp_cap.WithRespondWorkspaceConfiguration,
    LSPCapabilityClientBase,
):
    @property
    @override
    def language_id(self) -> lsp_type.LanguageKind:
        return lsp_type.LanguageKind.Python

    @override
    async def respond_workspace_configuration(
        self, req: lsp_type.ConfigurationRequest
    ) -> lsp_type.ConfigurationResponse:
        items = req.params.items

        config = [{} for _ in items]

        return lsp_type.ConfigurationResponse(
            id=req.id,
            result=config,
        )

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None):
        assert info, "Server info must be provided to check compatibility"

        version = info.version
        assert version, "Server version must be provided to check compatibility"

        # Remove any extra info after the version number
        version, _ = version.split(" ", 1)

        assert Version.parse(version).match(">=0.0.1-alpha.16")
        logger.debug(
            "Server version %s supports TyClient capabilities",
            version,
        )


@final
@dataclass(frozen=True)
class TyClient(LSPClientBase[TyCapabilityClient]):
    diagnostic_mode: Literal["openFilesOnly", "workspace"] = "openFilesOnly"
    log_level: Literal["error", "warn", "info", "debug", "trace"] = "info"
    import_strategy: Literal["fromEnvironment", "useBundled"] = "fromEnvironment"

    @property
    @override
    def server_cmd(self) -> Sequence[str]:
        return (
            "ty",
            "server",
        )

    @override
    @asynccontextmanager
    async def _start_client(
        self,
        server: LSPServerPool,
        workspace: Sequence[WorkspaceFolder],
    ) -> AsyncGenerator[TyCapabilityClient]:
        settings = [
            {
                "cwd": f.path,
                "workspace": f.uri,
                "importStrategy": self.import_strategy,
                "diagnosticMode": self.diagnostic_mode,
                "logLevel": self.log_level,
            }
            for f in workspace
        ]

        initialization_options = {
            "settings": settings,
        }

        async with TyCapabilityClient.start(
            server=server,
            args=BaseLSPCapabilityClientArgs(
                workspace_folders=workspace,
                initialization_options=initialization_options,
                sync_file=self.sync_file,
            ),
        ) as client:
            yield client
