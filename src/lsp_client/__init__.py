from __future__ import annotations

import lsprotocol.types as lsp_type
from loguru import logger

from . import capability as lsp_cap
from .client.base import LSPClient
from .server.base import LSPServer
from .types import Position, Range

# https://loguru.readthedocs.io/en/stable/overview.html#suitable-for-scripts-and-libraries
logger.disable("lsp_client")

__all__ = [
    "LSPClient",
    "LSPServer",
    "Position",
    "Range",
    "logger",
    "lsp_cap",
    "lsp_type",
]
