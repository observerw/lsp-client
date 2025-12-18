from __future__ import annotations

import shutil
from functools import partial
from subprocess import CalledProcessError
from typing import Any, override

import anyio
from attrs import define
from loguru import logger

from lsp_client.capability.request import (
    WithRequestCallHierarchy,
    WithRequestDefinition,
    WithRequestDocumentSymbol,
    WithRequestHover,
    WithRequestImplementation,
    WithRequestReferences,
    WithRequestTypeDefinition,
    WithRequestWorkspaceSymbol,
)
from lsp_client.capability.server_notification import (
    WithReceivePublishDiagnostics,
)
from lsp_client.capability.server_notification.log_message import WithReceiveLogMessage
from lsp_client.client.abc import LSPClient
from lsp_client.server.docker import DockerServer
from lsp_client.server.local import LocalServer
from lsp_client.utils.types import lsp_type

TsserverLocalServer = partial(
    LocalServer, command=["typescript-language-server", "--stdio"]
)
TsserverDockerServer = partial(DockerServer, image="docker.io/lspcontainers/tsserver")


@define
class TsserverClient(
    LSPClient,
    WithRequestHover,
    WithRequestDefinition,
    WithRequestReferences,
    WithRequestImplementation,
    WithRequestTypeDefinition,
    WithRequestCallHierarchy,
    WithRequestDocumentSymbol,
    WithRequestWorkspaceSymbol,
    WithReceiveLogMessage,
    WithReceivePublishDiagnostics,
):
    """
    - Language: TypeScript, JavaScript
    - Homepage: https://github.com/typescript-language-server/typescript-language-server
    - Doc: https://github.com/typescript-language-server/typescript-language-server#readme
    - Github: https://github.com/typescript-language-server/typescript-language-server
    - VSCode Extension: Built-in TypeScript support in VS Code
    """

    # Preferences for TypeScript/JavaScript language features
    suggest_complete_function_calls: bool = True
    include_automatic_optional_chain_completions: bool = True
    include_completions_for_module_exports: bool = True
    include_completions_with_insert_text: bool = True

    # Auto-import and path suggestions
    auto_import_suggestions: bool = True
    path_suggestions: bool = True

    # Code actions and refactorings
    enable_call_hierarchy: bool = True
    enable_semantic_highlighting: bool = True

    @override
    def get_language_id(self) -> lsp_type.LanguageKind:
        return lsp_type.LanguageKind.TypeScript

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

    @override
    async def ensure_installed(self) -> None:
        if shutil.which("typescript-language-server"):
            return

        logger.warning(
            "typescript-language-server not found, attempting to install via npm..."
        )

        try:
            await anyio.run_process(
                ["npm", "install", "-g", "typescript-language-server", "typescript"]
            )
            logger.info("Successfully installed typescript-language-server via npm")
            return
        except CalledProcessError as e:
            raise RuntimeError(
                "Could not install typescript-language-server. Please install it manually with 'npm install -g typescript-language-server typescript'. "
                "See https://github.com/typescript-language-server/typescript-language-server for more information."
            ) from e
