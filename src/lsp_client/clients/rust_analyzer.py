from __future__ import annotations

import shutil
from functools import partial
from subprocess import CalledProcessError
from typing import override

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
    WithRequestImplementation,
    WithRequestInlayHint,
    WithRequestPullDiagnostic,
    WithRequestReferences,
    WithRequestSignatureHelp,
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
    WithRespondInlayHintRefresh,
    WithRespondShowDocumentRequest,
    WithRespondShowMessageRequest,
    WithRespondWorkspaceFoldersRequest,
)
from lsp_client.clients.base import RustClientBase
from lsp_client.server import DefaultServers, ServerInstallationError
from lsp_client.server.container import ContainerServer
from lsp_client.server.local import LocalServer
from lsp_client.utils.config import ConfigurationMap
from lsp_client.utils.types import lsp_type

RustAnalyzerContainerServer = partial(
    ContainerServer, image="ghcr.io/lsp-client/rust-analyzer:latest"
)


async def ensure_rust_analyzer_installed() -> None:
    if shutil.which("rust-analyzer"):
        return

    logger.warning("rust-analyzer not found, attempting to install...")

    try:
        await anyio.run_process(["rustup", "component", "add", "rust-analyzer"])
        logger.info("Successfully installed rust-analyzer via rustup")
    except CalledProcessError as e:
        raise ServerInstallationError(
            "Could not install rust-analyzer. Please install it manually with 'rustup component add rust-analyzer'. "
            "See https://rust-analyzer.github.io/ for more information."
        ) from e


RustAnalyzerLocalServer = partial(
    LocalServer,
    program="rust-analyzer",
    args=[],
    ensure_installed=ensure_rust_analyzer_installed,
)


@define
class RustAnalyzerClient(
    RustClientBase,
    WithNotifyDidChangeConfiguration,
    WithRequestCallHierarchy,
    WithRequestCompletion,
    WithRequestDeclaration,
    WithRequestDefinition,
    WithRequestDocumentSymbol,
    WithRequestHover,
    WithRequestImplementation,
    WithRequestInlayHint,
    WithRequestPullDiagnostic,
    WithRequestReferences,
    WithRequestSignatureHelp,
    WithRequestTypeDefinition,
    WithRequestWorkspaceSymbol,
    WithReceiveLogMessage,
    WithReceiveLogTrace,
    WithReceivePublishDiagnostics,
    WithReceiveShowMessage,
    WithRespondConfigurationRequest,
    WithRespondInlayHintRefresh,
    WithRespondShowDocumentRequest,
    WithRespondShowMessageRequest,
    WithRespondWorkspaceFoldersRequest,
):
    """
    - Language: Rust
    - Homepage: https://rust-analyzer.github.io/
    - Doc: https://rust-analyzer.github.io/manual.html
    - Github: https://github.com/rust-lang/rust-analyzer
    - VSCode Extension: https://marketplace.visualstudio.com/items?itemName=rust-lang.rust-analyzer
    """

    @override
    def create_default_servers(self) -> DefaultServers:
        return DefaultServers(
            local=RustAnalyzerLocalServer(),
            container=RustAnalyzerContainerServer(),
        )

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        return

    @override
    def create_default_configuration_map(self) -> ConfigurationMap | None:
        """Create default configuration for rust-analyzer with all features enabled."""
        config_map = ConfigurationMap()
        config_map.update_global(
            {
                "rust-analyzer": {
                    # Enable inlay hints for all types
                    "inlayHints": {
                        "enable": True,
                        "chainingHints": {"enable": True},
                        "closureReturnTypeHints": {"enable": "always"},
                        "lifetimeElisionHints": {"enable": "always"},
                        "parameterHints": {"enable": True},
                        "reborrowHints": {"enable": "always"},
                        "renderColons": True,
                        "typeHints": {"enable": True},
                    },
                    # Enable diagnostics
                    "diagnostics": {
                        "enable": True,
                        "experimental": {"enable": True},
                    },
                    # Enable completion features
                    "completion": {
                        "autoimport": {"enable": True},
                        "autoself": {"enable": True},
                        "callable": {"snippets": "fill_arguments"},
                        "postfix": {"enable": True},
                        "privateEditable": {"enable": True},
                    },
                    # Enable checkOnSave with cargo check
                    "checkOnSave": {"enable": True},
                    # Enable code lens
                    "lens": {
                        "enable": True,
                        "run": {"enable": True},
                        "debug": {"enable": True},
                        "implementations": {"enable": True},
                        "references": {
                            "adt": {"enable": True},
                            "enumVariant": {"enable": True},
                            "method": {"enable": True},
                            "trait": {"enable": True},
                        },
                    },
                }
            }
        )
        return config_map
