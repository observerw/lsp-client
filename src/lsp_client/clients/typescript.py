from __future__ import annotations

import shutil
from functools import partial
from subprocess import CalledProcessError
from typing import Any, override

import anyio
from attrs import define
from loguru import logger

from lsp_client.capability.notification import (
    WithNotifyDidChangeConfiguration,
)
from lsp_client.capability.request import (
    WithRequestCompletion,
    WithRequestDefinition,
    WithRequestDocumentSymbol,
    WithRequestHover,
    WithRequestImplementation,
    WithRequestPullDiagnostic,
    WithRequestReferences,
    WithRequestTypeDefinition,
    WithRequestWorkspaceSymbol,
)
from lsp_client.capability.server_notification import (
    WithReceiveLogTrace,
    WithReceivePublishDiagnostics,
    WithReceiveShowMessage,
)
from lsp_client.capability.server_notification.log_message import WithReceiveLogMessage
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

TypescriptContainerServer = partial(
    ContainerServer, image="ghcr.io/observerw/lsp-client/typescript:latest"
)


async def ensure_typescript_installed() -> None:
    if shutil.which("typescript-language-server"):
        return

    logger.warning(
        "typescript-language-server not found, attempting to install via npm..."
    )

    try:
        # typescript-language-server requires the TypeScript compiler as a peer dependency
        # Reference: https://github.com/typescript-language-server/typescript-language-server#installing
        await anyio.run_process(
            ["npm", "install", "-g", "typescript-language-server", "typescript"]
        )
        logger.info("Successfully installed typescript-language-server via npm")
        return
    except CalledProcessError as e:
        raise ServerInstallationError(
            "Could not install typescript-language-server and typescript. Please install them manually with 'npm install -g typescript-language-server typescript'. "
            "See https://github.com/typescript-language-server/typescript-language-server for more information."
        ) from e


TypescriptLocalServer = partial(
    LocalServer,
    program="typescript-language-server",
    args=["--stdio"],
    ensure_installed=ensure_typescript_installed,
)


@define
class TypescriptClient(
    Client,
    WithNotifyDidChangeConfiguration,
    WithRequestCompletion,
    WithRequestHover,
    WithRequestDefinition,
    WithRequestReferences,
    WithRequestImplementation,
    WithRequestTypeDefinition,
    WithRequestDocumentSymbol,
    WithRequestPullDiagnostic,
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
    - Language: TypeScript, JavaScript
    - Homepage: https://github.com/typescript-language-server/typescript-language-server
    - Doc: https://github.com/typescript-language-server/typescript-language-server#readme
    - Github: https://github.com/typescript-language-server/typescript-language-server
    - VSCode Extension: Built-in TypeScript support in VS Code
    """

    # Preferences for TypeScript/JavaScript language features
    # Reference: https://github.com/typescript-language-server/typescript-language-server#initializationoptions
    suggest_complete_function_calls: bool = True
    include_automatic_optional_chain_completions: bool = True
    include_completions_for_module_exports: bool = True
    include_completions_with_insert_text: bool = True

    @override
    def get_language_id(self) -> lsp_type.LanguageKind:
        return lsp_type.LanguageKind.TypeScript

    @override
    def create_default_servers(self) -> DefaultServers:
        return DefaultServers(
            local=TypescriptLocalServer(),
            container=TypescriptContainerServer(),
        )

    @override
    def create_initialization_options(self) -> dict[str, Any]:
        return {
            "preferences": {
                "includeCompletionsForModuleExports": self.include_completions_for_module_exports,
                "includeAutomaticOptionalChainCompletions": self.include_automatic_optional_chain_completions,
                "includeCompletionsWithInsertText": self.include_completions_with_insert_text,
            },
            "suggest": {
                "completeFunctionCalls": self.suggest_complete_function_calls,
            },
        }

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        return
