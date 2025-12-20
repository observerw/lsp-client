from __future__ import annotations

import shutil
from functools import partial
from subprocess import CalledProcessError
from typing import Any, Literal, override

import anyio
from attrs import Factory, define
from loguru import logger

from lsp_client.capability.notification import (
    WithNotifyDidChangeConfiguration,
)
from lsp_client.capability.request import (
    WithRequestCallHierarchy,
    WithRequestDeclaration,
    WithRequestDefinition,
    WithRequestDocumentSymbol,
    WithRequestHover,
    WithRequestImplementation,
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
from lsp_client.client.abc import LSPClient
from lsp_client.server.abc import LSPServer
from lsp_client.server.container import ContainerServer
from lsp_client.server.local import LocalServer
from lsp_client.utils.types import lsp_type

RustAnalyzerContainerServer = partial(
    ContainerServer, image="ghcr.io/observerw/lsp-client/rust-analyzer:latest"
)


@define
class RustAnalyzerClient(
    LSPClient,
    WithNotifyDidChangeConfiguration,
    WithRequestCallHierarchy,
    WithRequestDeclaration,
    WithRequestDefinition,
    WithRequestDocumentSymbol,
    WithRequestHover,
    WithRequestImplementation,
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
    proc_macro_enable: bool = True
    cargo_build_scripts_enable: bool = True

    check_command: Literal["check", "clippy"] = "check"
    check_all_targets: bool = True
    check_extra_args: list[str] = Factory(list)
    check_extra_env: dict[str, str] = Factory(dict)

    diagnostics_enable: bool = True

    cargo_features: list[str] = Factory(list)
    cargo_extra_args: list[str] = Factory(list)
    cargo_extra_env: dict[str, str] = Factory(dict)

    @override
    def get_language_id(self) -> lsp_type.LanguageKind:
        return lsp_type.LanguageKind.Rust

    @override
    def create_default_server(self) -> LSPServer:
        return LocalServer(command=["rust-analyzer"])

    @override
    def create_initialization_options(self) -> dict[str, Any]:
        return {
            "procMacro": {"enable": self.proc_macro_enable},
            "cargo": {
                "buildScripts": {"enable": self.cargo_build_scripts_enable},
                "features": list(self.cargo_features),
                "extraArgs": list(self.cargo_extra_args),
                "extraEnv": dict(self.cargo_extra_env),
            },
            "check": {
                "command": self.check_command,
                "allTargets": self.check_all_targets,
                "extraArgs": list(self.check_extra_args),
                "extraEnv": dict(self.check_extra_env),
            },
            "diagnostics": {"enable": self.diagnostics_enable},
        }

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        return

    @override
    async def ensure_installed(self) -> None:
        if shutil.which("rust-analyzer"):
            return

        logger.warning("rust-analyzer not found, attempting to install...")

        try:
            await anyio.run_process(["rustup", "component", "add", "rust-analyzer"])
            logger.info("Successfully installed rust-analyzer via rustup")
        except CalledProcessError as e:
            raise RuntimeError(
                "Could not install rust-analyzer. Please install it manually with 'rustup component add rust-analyzer'. "
                "See https://rust-analyzer.github.io/ for more information."
            ) from e
