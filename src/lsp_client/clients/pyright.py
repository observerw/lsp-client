from __future__ import annotations

import shutil
from functools import partial
from subprocess import CalledProcessError
from typing import Any, Literal, override

import anyio
from attrs import define
from loguru import logger

from lsp_client.capability.request import WithRequestDefinition, WithRequestReferences
from lsp_client.capability.server_notification import WithReceivePublishDiagnostics
from lsp_client.capability.server_notification.log_message import WithReceiveLogMessage
from lsp_client.client.abc import LSPClient
from lsp_client.server.docker import DockerServer
from lsp_client.server.local import LocalServer
from lsp_client.utils.types import lsp_type

PyrightLocalServer = partial(LocalServer, command=["pyright-langserver"])
PyrightDockerServer = partial(
    DockerServer, image="docker.io/lspcontainers/pyright-langserver"
)


@define
class PyrightClient(
    LSPClient,
    WithRequestReferences,
    WithRequestDefinition,
    WithReceiveLogMessage,
    WithReceivePublishDiagnostics,
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
    def create_initialization_options(self) -> dict[str, Any]:
        return {
            "diagnosticMode": self.diagnostic_mode,
            "disablePullDiagnostics": self.disable_pull_diagnostics,
        }

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        return

    @override
    async def ensure_installed(self) -> None:
        if shutil.which("pyright-langserver"):
            return

        logger.warning("pyright-langserver not found, attempting to install via npm...")

        try:
            await anyio.run_process(["npm", "install", "-g", "pyright"])
            logger.info("Successfully installed pyright-langserver via npm")
            return
        except CalledProcessError as e:
            raise RuntimeError(
                "Could not install pyright-langserver. Please install it manually with 'npm install -g pyright'. "
                "See https://microsoft.github.io/pyright/ for more information."
            ) from e
