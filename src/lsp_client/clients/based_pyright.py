"""
basedpyright: Language Server for Python - https://docs.basedpyright.com
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, final, override

from attrs import Factory, define
from loguru import logger
from semver import Version

from lsp_client import LSPClient, LSPServer, lsp_cap, lsp_type


@final
@define
class BasedPyrightServer(LSPServer):
    @property
    @override
    def server_cmd(self) -> Sequence[str]:
        return ("basedpyright-langserver",)

    @property
    @override
    def server_args(self) -> Sequence[str]:
        return ("--stdio",)


@final
@define
class BasedPyrightClient(
    lsp_cap.FullFeaturedCapabilityGroup,
    lsp_cap.WithRequestWorkspaceSymbolInformation,
    lsp_cap.WithRequestDocumentBaseSymbols,
    LSPClient[BasedPyrightServer],
):
    server: BasedPyrightServer = Factory(BasedPyrightServer)

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
