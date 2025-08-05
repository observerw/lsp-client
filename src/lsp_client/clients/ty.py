"""
ty: Type checker and language server for Python - https://docs.astral.sh/ty/

References:
    - VSCode Extension: https://github.com/astral-sh/ty-vscode
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Literal, final, override

from loguru import logger
from semver import Version

from lsp_client import (
    ClientArgs,
    ClientRuntimeArgs,
    LSPCapabilityClientBase,
    LSPClientBase,
    lsp_cap,
    lsp_type,
)


@dataclass(frozen=True)
class TyConfig:
    diagnostic_mode: Literal["openFilesOnly", "workspace"] = "openFilesOnly"
    log_level: Literal["error", "warn", "info", "debug", "trace"] = "info"
    import_strategy: Literal["fromEnvironment", "useBundled"] = "fromEnvironment"


@final
@dataclass
class TyCapabilityClient(
    lsp_cap.WithRequestReferences,
    lsp_cap.WithRespondWorkspaceConfiguration,
    LSPCapabilityClientBase[TyConfig],
):
    @property
    @override
    def language_id(self) -> lsp_type.LanguageKind:
        return lsp_type.LanguageKind.Python

    @property
    @override
    def initialization_options(self) -> dict[str, Any]:
        if not (config := self._extra):
            return {}

        return {
            "settings": [
                {
                    "cwd": f.path,
                    "workspace": f.uri,
                    "importStrategy": config.import_strategy,
                    "diagnosticMode": config.diagnostic_mode,
                    "logLevel": config.log_level,
                }
                for f in self.workspace.values()
            ]
        }

    @override
    async def respond_workspace_configuration(
        self, req: lsp_type.ConfigurationRequest
    ) -> lsp_type.ConfigurationResponse:
        items = req.params.items

        # TODO handle workspace/configuration request
        config = [{} for _ in items]

        return lsp_type.ConfigurationResponse(
            id=req.id,
            result=config,
        )

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None):
        assert info, "Server info must be provided to check compatibility"

        version = info.version
        assert version, "Server version must be provided to check compatibility"

        # Remove any extra info after the version number
        version, _ = version.split(" ", 1)

        assert Version.parse(version).match(">=0.0.1-alpha.16")
        logger.debug(
            "Server version %s supports TyClient capabilities",
            version,
        )


@final
@dataclass(frozen=True)
class TyClient(LSPClientBase[TyCapabilityClient]):
    config: TyConfig = TyConfig()

    @property
    @override
    def server_cmd(self) -> Sequence[str]:
        return (
            "ty",
            "server",
        )

    @override
    @asynccontextmanager
    async def _start_client(
        self,
        args: ClientArgs,
        runtime_args: ClientRuntimeArgs,
    ) -> AsyncGenerator[TyCapabilityClient]:
        async with TyCapabilityClient.start(
            args=args,
            runtime_args=runtime_args,
            extra=self.config,
        ) as client:
            yield client
