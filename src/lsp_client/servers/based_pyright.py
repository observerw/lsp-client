"""
basedpyright: Language Server for Python - https://docs.basedpyright.com
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import ClassVar, override

from semver import Version

from lsp_client import lsp_type
from lsp_client.capability.group import FullFeaturedCapabilityGroup
from lsp_client.client import LSPClientBase

logger = logging.getLogger(__name__)


class BasedPyrightClient(
    FullFeaturedCapabilityGroup,
    LSPClientBase,
):
    language_id: ClassVar[lsp_type.LanguageKind] = lsp_type.LanguageKind.Python
    server_cmd: ClassVar[Sequence[str]] = (
        "basedpyright-langserver",
        "--stdio",
    )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        if info and (version := info.version):
            assert Version.parse(version).match(">=1.29")
            logger.debug(
                "Server version %s supports BasedPyrightClient capabilities",
                version,
            )
