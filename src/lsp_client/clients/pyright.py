from __future__ import annotations

import shutil
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
    WithRequestCallHierarchy,
    WithRequestCompletion,
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

PyrightContainerServer = partial(
    ContainerServer, image="ghcr.io/observerw/lsp-client/pyright:latest"
)


async def ensure_pyright_installed() -> None:
    if shutil.which("pyright-langserver"):
        return

    logger.warning("pyright-langserver not found, attempting to install via npm...")

    try:
        await anyio.run_process(["npm", "install", "-g", "pyright"])
        logger.info("Successfully installed pyright-langserver via npm")
        return
    except CalledProcessError as e:
        raise ServerInstallationError(
            "Could not install pyright-langserver. Please install it manually with 'npm install -g pyright'. "
            "See https://microsoft.github.io/pyright/ for more information."
        ) from e


PyrightLocalServer = partial(
    LocalServer,
    program="pyright-langserver",
    args=["--stdio"],
    ensure_installed=ensure_pyright_installed,
)


@define
class PyrightClient(
    Client,
    WithNotifyDidChangeConfiguration,
    WithRequestCallHierarchy,
    WithRequestCompletion,
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
    - Homepage: https://microsoft.github.io/pyright/
    - Doc: https://microsoft.github.io/pyright/
    - Github: https://github.com/microsoft/pyright
    - VSCode Extension: https://github.com/microsoft/pyright/tree/main/packages/vscode-pyright
    """

    diagnostic_mode: Literal["openFilesOnly", "workspace"] = "workspace"
    disable_pull_diagnostics: bool = False

    @override
    def get_language_id(self) -> lsp_type.LanguageKind:
        return lsp_type.LanguageKind.Python

    @override
    def create_default_servers(self) -> DefaultServers:
        return DefaultServers(
            local=PyrightLocalServer(),
            container=PyrightContainerServer(),
        )

    @override
    def create_initialization_options(self) -> dict[str, Any]:
        return {
            "diagnosticMode": self.diagnostic_mode,
            "disablePullDiagnostics": self.disable_pull_diagnostics,
        }

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        return
