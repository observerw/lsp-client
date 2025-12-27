from __future__ import annotations

import shutil
from functools import partial
from subprocess import CalledProcessError
from typing import override

import anyio
from attrs import define
from loguru import logger

from lsp_client.capability.notification import WithNotifyDidChangeConfiguration
from lsp_client.capability.request import (
    WithRequestCallHierarchy,
    WithRequestCompletion,
    WithRequestDefinition,
    WithRequestDocumentSymbol,
    WithRequestHover,
    WithRequestImplementation,
    WithRequestInlayHint,
    WithRequestReferences,
    WithRequestSignatureHelp,
    WithRequestTypeDefinition,
    WithRequestTypeHierarchy,
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
from lsp_client.clients.base import GoClientBase
from lsp_client.server import DefaultServers, ServerInstallationError
from lsp_client.server.container import ContainerServer
from lsp_client.server.local import LocalServer
from lsp_client.utils.config import ConfigurationMap
from lsp_client.utils.types import lsp_type

GoplsContainerServer = partial(ContainerServer, image="ghcr.io/lsp-client/gopls:latest")


async def ensure_gopls_installed() -> None:
    if shutil.which("gopls"):
        return

    logger.warning("gopls not found, attempting to install via go install...")

    try:
        await anyio.run_process(["go", "install", "golang.org/x/tools/gopls@latest"])
        logger.info("Successfully installed gopls via go install")
        return
    except CalledProcessError as e:
        raise ServerInstallationError(
            "Could not install gopls. Please install it manually with 'go install golang.org/x/tools/gopls@latest'. "
            "See https://github.com/golang/tools/tree/master/gopls for more information."
        ) from e


GoplsLocalServer = partial(
    LocalServer,
    program="gopls",
    args=["serve"],
    ensure_installed=ensure_gopls_installed,
)


@define
class GoplsClient(
    GoClientBase,
    WithNotifyDidChangeConfiguration,
    WithRequestCallHierarchy,
    WithRequestCompletion,
    WithRequestDefinition,
    WithRequestDocumentSymbol,
    WithRequestHover,
    WithRequestImplementation,
    WithRequestInlayHint,
    WithRequestReferences,
    WithRequestSignatureHelp,
    WithRequestTypeDefinition,
    WithRequestTypeHierarchy,
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
    - Language: Go
    - Homepage: https://pkg.go.dev/golang.org/x/tools/gopls
    - Doc: https://github.com/golang/tools/blob/master/gopls/README.md
    - Github: https://github.com/golang/tools/tree/master/gopls
    - VSCode Extension: https://marketplace.visualstudio.com/items?itemName=golang.go
    """

    @override
    def create_default_servers(self) -> DefaultServers:
        return DefaultServers(
            local=GoplsLocalServer(),
            container=GoplsContainerServer(),
        )

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        return

    @override
    def create_default_configuration_map(self) -> ConfigurationMap | None:
        """Create default configuration for gopls with all features enabled."""
        config_map = ConfigurationMap()
        config_map.update_global(
            {
                "gopls": {
                    # Enable inlay hints
                    "hints": {
                        "assignVariableTypes": True,
                        "compositeLiteralFields": True,
                        "compositeLiteralTypes": True,
                        "constantValues": True,
                        "functionTypeParameters": True,
                        "parameterNames": True,
                        "rangeVariableTypes": True,
                    },
                    # Enable code lenses
                    "codelenses": {
                        "gc_details": True,
                        "generate": True,
                        "regenerate_cgo": True,
                        "run_govulncheck": True,
                        "test": True,
                        "tidy": True,
                        "upgrade_dependency": True,
                        "vendor": True,
                    },
                    # Enable diagnostics
                    "diagnosticsDelay": "250ms",
                    "analyses": {
                        "fieldalignment": True,
                        "nilness": True,
                        "unusedparams": True,
                        "unusedwrite": True,
                        "useany": True,
                    },
                    # Enable completion features
                    "completionDocumentation": True,
                    "deepCompletion": True,
                    "matcher": "Fuzzy",
                    "usePlaceholders": True,
                    # Enable semantic tokens
                    "semanticTokens": True,
                }
            }
        )
        return config_map
