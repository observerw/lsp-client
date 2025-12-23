from __future__ import annotations

import shutil
from functools import partial
from subprocess import CalledProcessError
from typing import Any, override

import anyio
from attrs import Factory, define
from loguru import logger

from lsp_client.capability.request import (
    WithRequestCallHierarchy,
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
    WithReceivePublishDiagnostics,
)
from lsp_client.capability.server_notification.log_message import WithReceiveLogMessage
from lsp_client.client.abc import Client
from lsp_client.server import DefaultServers, ServerInstallationError
from lsp_client.server.container import ContainerServer
from lsp_client.server.local import LocalServer
from lsp_client.utils.types import lsp_type

from .extension import (
    WithReceiveDenoRegistryStatus,
    WithReceiveDenoTestModule,
    WithReceiveDenoTestModuleDelete,
    WithReceiveDenoTestRunProgress,
    WithRequestDenoCache,
    WithRequestDenoPerformance,
    WithRequestDenoReloadImportRegistries,
    WithRequestDenoTask,
    WithRequestDenoTestRun,
    WithRequestDenoTestRunCancel,
    WithRequestDenoVirtualTextDocument,
)

DenoContainerServer = partial(ContainerServer, image="ghcr.io/lsp-client/deno:latest")


async def ensure_deno_installed() -> None:
    if shutil.which("deno"):
        return

    logger.warning("deno not found, attempting to install...")

    try:
        # Use shell to execute the piped command
        await anyio.run_process(
            ["sh", "-c", "curl -fsSL https://deno.land/install.sh | sh"]
        )
        logger.info("Successfully installed deno via shell script")
        return
    except CalledProcessError as e:
        raise ServerInstallationError(
            "Could not install deno. Please install it manually with:\n"
            "curl -fsSL https://deno.land/install.sh | sh\n\n"
            "See https://deno.land/ for more information."
        ) from e


DenoLocalServer = partial(
    LocalServer,
    program="deno",
    args=["lsp"],
    ensure_installed=ensure_deno_installed,
)


@define
class DenoClient(
    Client,
    WithRequestHover,
    WithRequestCompletion,
    WithRequestDefinition,
    WithRequestReferences,
    WithRequestImplementation,
    WithRequestTypeDefinition,
    WithRequestCallHierarchy,
    WithRequestDocumentSymbol,
    WithRequestPullDiagnostic,
    WithRequestWorkspaceSymbol,
    WithReceiveLogMessage,
    WithReceivePublishDiagnostics,
    WithRequestDenoCache,
    WithRequestDenoPerformance,
    WithRequestDenoReloadImportRegistries,
    WithRequestDenoVirtualTextDocument,
    WithRequestDenoTask,
    WithRequestDenoTestRun,
    WithRequestDenoTestRunCancel,
    WithReceiveDenoRegistryStatus,
    WithReceiveDenoTestModule,
    WithReceiveDenoTestModuleDelete,
    WithReceiveDenoTestRunProgress,
):
    """
    - Language: TypeScript, JavaScript
    - Homepage: https://deno.land/
    - Doc: https://docs.deno.com/runtime/reference/lsp_integration/
    - Github: https://github.com/denoland/deno
    - VSCode Extension: https://marketplace.visualstudio.com/items?itemName=denoland.vscode-deno
    """

    enable: bool = True
    unstable: bool = False
    lint: bool = True

    config: str | None = None
    import_map: str | None = None

    code_lens_implementations: bool = True
    code_lens_references: bool = True
    code_lens_references_all_functions: bool = True
    code_lens_test: bool = True

    suggest_complete_function_calls: bool = True
    suggest_names: bool = True
    suggest_paths: bool = True
    suggest_auto_imports: bool = True
    suggest_imports_auto_discover: bool = True
    suggest_imports_hosts: list[str] = Factory(list)

    testing_enable: bool = False
    testing_args: list[str] = Factory(list)

    @override
    def get_language_id(self) -> lsp_type.LanguageKind:
        return lsp_type.LanguageKind.TypeScript

    @override
    def create_default_servers(self) -> DefaultServers:
        return DefaultServers(
            local=DenoLocalServer(),
            container=DenoContainerServer(),
        )

    @override
    def create_initialization_options(self) -> dict[str, Any]:
        options: dict[str, Any] = {
            "enable": self.enable,
            "unstable": self.unstable,
            "lint": self.lint,
            "codeLens": {
                "implementations": self.code_lens_implementations,
                "references": self.code_lens_references,
                "referencesAllFunctions": self.code_lens_references_all_functions,
                "test": self.code_lens_test,
            },
            "suggest": {
                "completeFunctionCalls": self.suggest_complete_function_calls,
                "names": self.suggest_names,
                "paths": self.suggest_paths,
                "autoImports": self.suggest_auto_imports,
                "imports": {
                    "autoDiscover": self.suggest_imports_auto_discover,
                    "hosts": list(self.suggest_imports_hosts),
                },
            },
        }

        if self.config:
            options["config"] = self.config

        if self.import_map:
            options["importMap"] = self.import_map

        if self.testing_enable:
            options["testing"] = {
                "enable": self.testing_enable,
                "args": list(self.testing_args),
            }

        return options

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        return
