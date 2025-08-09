"""
basedpyright: Language Server for Python - https://docs.basedpyright.com
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, final, override

from loguru import logger
from semver import Version

from lsp_client import lsp_cap, lsp_type
from lsp_client.client.stdio import DockerStdioClient
from lsp_client.server.stdio import DockerStdioServer, StdioServer


@final
@dataclass(kw_only=True)
class BasedPyrightServer(StdioServer):
    @property
    @override
    def server_cmd(self) -> Sequence[str]:
        return (
            "basedpyright-langserver",
            "--stdio",
        )


@final
@dataclass(kw_only=True)
class BasedPyrightDockerServer(DockerStdioServer):
    @property
    @override
    def docker_args(self) -> Sequence[str]:
        return (
            "mcr.microsoft.com/pyright/langserver:1.29.0",
            "--stdio",
        )


@final
@dataclass(kw_only=True)
class BasedPyrightClient(
    lsp_cap.FullFeaturedCapabilityGroup,
    lsp_cap.WithRequestWorkspaceSymbolInformation,
    lsp_cap.WithRequestDocumentBaseSymbols,
    DockerStdioClient,
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
            "Server version {} supports BasedPyrightClient capabilities",
            version,
        )

    @override
    def create_initialization_options(self) -> dict[str, Any] | None:
        return None

    @override
    def create_server(self) -> StdioServer:
        Server = BasedPyrightDockerServer if self.docker else BasedPyrightServer
        return Server(
            process_count=self.server_count,
            info=self.server_info,
        )
