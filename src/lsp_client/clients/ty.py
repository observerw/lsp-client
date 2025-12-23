from __future__ import annotations

import shutil
import sys
from functools import partial
from subprocess import CalledProcessError
from typing import Any, Literal, override

import anyio
from attrs import define
from loguru import logger

from lsp_client.capability.notification import (
    WithNotifyDidChangeConfiguration,
)
from lsp_client.capability.request import (
    WithRequestDeclaration,
    WithRequestDefinition,
    WithRequestDocumentSymbol,
    WithRequestHover,
    WithRequestPullDiagnostic,
    WithRequestReferences,
    WithRequestTypeDefinition,
    WithRequestWorkspaceSymbol,
)
from lsp_client.capability.server_notification import (
    WithReceiveLogMessage,
    WithReceiveLogTrace,
    WithReceivePublishDiagnostics,
    WithReceiveShowMessage,
)
from lsp_client.capability.server_request import (
    WithRespondConfigurationRequest,
    WithRespondShowDocumentRequest,
    WithRespondShowMessageRequest,
    WithRespondWorkspaceFoldersRequest,
)
from lsp_client.client.abc import Client
from lsp_client.server import DefaultServers, ServerInstallationError
from lsp_client.server.container import ContainerServer
from lsp_client.server.local import LocalServer
from lsp_client.utils.types import lsp_type

TyContainerServer = partial(ContainerServer, image="ghcr.io/astral-sh/ty:latest")


async def ensure_ty_installed() -> None:
    if shutil.which("ty"):
        return

    logger.warning("ty not found, attempting to install via pip...")

    try:
        await anyio.run_process([sys.executable, "-m", "pip", "install", "ty"])
        logger.info("Successfully installed ty via pip")
        return
    except CalledProcessError as e:
        raise ServerInstallationError(
            "Could not install ty. Please install it manually with 'pip install ty' or 'uv tool install ty'. "
            "See https://docs.astral.sh/ty/installation/ for more information."
        ) from e


TyLocalServer = partial(
    LocalServer,
    program="ty",
    args=["server"],
    ensure_installed=ensure_ty_installed,
)


@define
class TyClient(
    Client,
    WithNotifyDidChangeConfiguration,
    WithRequestDeclaration,
    WithRequestDefinition,
    WithRequestDocumentSymbol,
    WithRequestHover,
    WithRequestPullDiagnostic,
    WithRequestReferences,
    WithRequestTypeDefinition,
    WithRequestWorkspaceSymbol,
    WithReceiveLogMessage,
    WithReceiveLogTrace,
    WithReceivePublishDiagnostics,
    WithReceiveShowMessage,
    WithRespondConfigurationRequest,
    WithRespondShowDocumentRequest,
    WithRespondShowMessageRequest,
    WithRespondWorkspaceFoldersRequest,
):
    """
    - Language: Python
    - Homepage: https://docs.astral.sh/ty/
    - Doc: https://docs.astral.sh/ty/
    - Github: https://github.com/astral-sh/ty
    - VSCode Extension: https://docs.astral.sh/ty/editors/vscode/
    """

    log_level: Literal["trace", "debug", "info", "warn", "error"] = "info"
    diagnostic_mode: Literal["openFilesOnly", "workspace"] = "openFilesOnly"
    inlay_hints_variable_types: bool = True
    inlay_hints_call_argument_names: bool = True

    @override
    def get_language_id(self) -> lsp_type.LanguageKind:
        return lsp_type.LanguageKind.Python

    @override
    def create_default_servers(self) -> DefaultServers:
        return DefaultServers(
            local=TyLocalServer(),
            container=TyContainerServer(),
        )

    @override
    def create_initialization_options(self) -> dict[str, Any]:
        return {
            "logLevel": self.log_level,
            "diagnosticMode": self.diagnostic_mode,
            "inlayHints": {
                "variableTypes": self.inlay_hints_variable_types,
                "callArgumentNames": self.inlay_hints_call_argument_names,
            },
        }

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        return
