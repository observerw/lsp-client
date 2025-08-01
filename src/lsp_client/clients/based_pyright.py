"""
basedpyright: Language Server for Python - https://docs.basedpyright.com
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import override

from semver import Version

from lsp_client import lsp_type
from lsp_client.capability.client import LSPCapabilityClientBase
from lsp_client.capability.group import FullFeaturedCapabilityGroup
from lsp_client.client import LSPClientBase

logger = logging.getLogger(__name__)


class BasedPyrightCapabilityClient(
    FullFeaturedCapabilityGroup,
    LSPCapabilityClientBase,
):
    @property
    @override
    def language_id(self) -> lsp_type.LanguageKind:
        return lsp_type.LanguageKind.Python

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None):
        assert info, "Server info must be provided to check compatibility"

        version = info.version
        assert version, "Server version is required for compatibility check"

        assert Version.parse(version).match(">=1.29")
        logger.debug(
            "Server version %s supports BasedPyrightClient capabilities",
            version,
        )


class BasedPyrightClient(LSPClientBase[BasedPyrightCapabilityClient]):
    @property
    @override
    def cap(self) -> type[BasedPyrightCapabilityClient]:
        return BasedPyrightCapabilityClient

    @property
    @override
    def server_cmd(self) -> Sequence[str]:
        return (
            "basedpyright-langserver",
            "--stdio",
        )
