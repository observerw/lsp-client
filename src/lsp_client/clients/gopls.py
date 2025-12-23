from __future__ import annotations

import shutil
from functools import partial
from subprocess import CalledProcessError
from typing import Any, Literal, override

import anyio
from attrs import define, field
from loguru import logger

from lsp_client.capability.notification import (
    WithNotifyDidChangeConfiguration,
)
from lsp_client.capability.request import (
    WithRequestCallHierarchy,
    WithRequestDefinition,
    WithRequestDocumentSymbol,
    WithRequestHover,
    WithRequestImplementation,
    WithRequestReferences,
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
    WithRespondShowDocumentRequest,
    WithRespondShowMessageRequest,
    WithRespondWorkspaceFoldersRequest,
)
from lsp_client.client.abc import Client
from lsp_client.server import DefaultServers, ServerInstallationError
from lsp_client.server.container import ContainerServer
from lsp_client.server.local import LocalServer
from lsp_client.utils.types import lsp_type

GoplsContainerServer = partial(
    ContainerServer, image="ghcr.io/observerw/lsp-client/gopls:latest"
)


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
    Client,
    WithNotifyDidChangeConfiguration,
    WithRequestCallHierarchy,
    WithRequestDefinition,
    WithRequestDocumentSymbol,
    WithRequestHover,
    WithRequestImplementation,
    WithRequestReferences,
    WithRequestTypeDefinition,
    WithRequestTypeHierarchy,
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
    - Language: Go
    - Homepage: https://pkg.go.dev/golang.org/x/tools/gopls
    - Doc: https://github.com/golang/tools/blob/master/gopls/README.md
    - Github: https://github.com/golang/tools/tree/master/gopls
    - VSCode Extension: https://marketplace.visualstudio.com/items?itemName=golang.go
    """

    all_experiments: bool = False
    analyses: dict[str, bool | str] = field(factory=dict)
    allow_modfile_mods: bool = False
    allow_multi_line_string_literals: bool = False
    allow_implicit_variable_assignments: bool = False
    build_directory: str | None = None
    codelenses: dict[str, bool] = field(factory=dict)
    complete_completions: bool = False
    complete_unimported: bool = False
    completion_budget: str = "500ms"
    diagnostics_delay: str = "500ms"
    documentation_options: dict[str, bool] = field(factory=dict)
    experimental_postfix_completions: bool = True
    experimental_prefixed_format: bool = True
    experimental_template_support: bool = False
    experimental_workspace_module: bool = False
    gofumpt: bool = False
    hover_kind: Literal[
        "FullDocumentation", "NoDocumentation", "SingleLine", "Structured"
    ] = "FullDocumentation"
    link_in_hover: bool = True
    link_target: str = "pkg.go.dev"
    matcher: Literal["Fuzzy", "CaseInsensitive", "CaseSensitive"] = "Fuzzy"
    semantic_tokens: bool = True
    staticcheck: bool = False
    use_placeholders: bool = False
    verbose_output: bool = False

    @override
    def get_language_id(self) -> lsp_type.LanguageKind:
        return lsp_type.LanguageKind.Go

    @override
    def create_default_servers(self) -> DefaultServers:
        return DefaultServers(
            local=GoplsLocalServer(),
            container=GoplsContainerServer(),
        )

    @override
    def create_initialization_options(self) -> dict[str, Any]:
        options: dict[str, Any] = {}

        if self.all_experiments:
            options["allExperiments"] = self.all_experiments

        if self.analyses:
            options["analyses"] = self.analyses

        if self.allow_modfile_mods:
            options["allowModfileMods"] = self.allow_modfile_mods

        if self.allow_multi_line_string_literals:
            options["allowMultiLineStringLiterals"] = (
                self.allow_multi_line_string_literals
            )

        if self.allow_implicit_variable_assignments:
            options["allowImplicitVariableAssignments"] = (
                self.allow_implicit_variable_assignments
            )

        if self.build_directory:
            options["buildDirectory"] = self.build_directory

        if self.codelenses:
            options["codelenses"] = self.codelenses

        if self.complete_completions:
            options["completeCompletions"] = self.complete_completions

        if self.complete_unimported:
            options["completeUnimported"] = self.complete_unimported

        if self.completion_budget:
            options["completionBudget"] = self.completion_budget

        if self.diagnostics_delay:
            options["diagnosticsDelay"] = self.diagnostics_delay

        if self.documentation_options:
            options["documentationOptions"] = self.documentation_options

        options["experimentalPostfixCompletions"] = (
            self.experimental_postfix_completions
        )
        options["experimentalPrefixedFormat"] = self.experimental_prefixed_format
        options["experimentalTemplateSupport"] = self.experimental_template_support
        options["experimentalWorkspaceModule"] = self.experimental_workspace_module
        options["gofumpt"] = self.gofumpt
        options["hoverKind"] = self.hover_kind
        options["linkInHover"] = self.link_in_hover
        options["linkTarget"] = self.link_target
        options["matcher"] = self.matcher
        options["semanticTokens"] = self.semantic_tokens
        options["staticcheck"] = self.staticcheck
        options["usePlaceholders"] = self.use_placeholders
        options["verboseOutput"] = self.verbose_output

        return options

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        return
