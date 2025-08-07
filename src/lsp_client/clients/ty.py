"""
ty: Type checker and language server for Python - https://docs.astral.sh/ty/

References:
    - VSCode Extension: https://github.com/astral-sh/ty-vscode
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal, final, override

from loguru import logger
from semver import Version

from lsp_client import lsp_cap, lsp_type
from lsp_client.client.stdio import StdioClient
from lsp_client.server.stdio import StdioServer


@final
@dataclass(kw_only=True)
class TyServer(StdioServer):
    @property
    @override
    def server_cmd(self) -> Sequence[str]:
        return (
            "ty",
            "server",
        )


@final
@dataclass(kw_only=True)
class TyClient(
    lsp_cap.WithRequestReferences,
    lsp_cap.WithRespondWorkspaceConfiguration,
    lsp_cap.WithReceivePublishDiagnostics,
    StdioClient,
):
    diagnostic_mode: Literal["openFilesOnly", "workspace"] = "openFilesOnly"
    log_level: Literal["error", "warn", "info", "debug", "trace"] = "info"
    import_strategy: Literal["fromEnvironment", "useBundled"] = "fromEnvironment"

    @property
    @override
    def language_id(self) -> lsp_type.LanguageKind:
        return lsp_type.LanguageKind.Python

    @override
    def create_server(self) -> StdioServer:
        return TyServer(
            process_count=self.server_count,
            info=self.server_info,
        )

    @override
    def create_initialization_options(self) -> dict[str, Any] | None:
        return {
            "settings": [
                {
                    "cwd": f.path,
                    "workspace": f.uri,
                    "importStrategy": self.import_strategy,
                    "diagnosticMode": self.diagnostic_mode,
                    "logLevel": self.log_level,
                }
                for f in self.workspace_folders
            ]
        }

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None):
        assert info, "Server info must be provided to check compatibility"

        version = info.version
        assert version, "Server version must be provided to check compatibility"

        # Remove any extra info after the version number
        version, _ = version.split(" ", 1)

        assert Version.parse(version).match(">=0.0.1-alpha.16")
        logger.debug(
            "Server version {} supports TyClient capabilities",
            version,
        )

    @override
    async def respond_workspace_configuration(
        self, req: lsp_type.ConfigurationRequest
    ) -> lsp_type.ConfigurationResponse:
        items = req.params.items

        # TODO handle workspace/configuration request
        config = [{} for _ in items]

        return lsp_type.ConfigurationResponse(
            id=req.id,
            result=config,
        )
