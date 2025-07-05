"""
ty Static Type Checker for Python - https://github.com/astral-sh/ty
"""

from typing import ClassVar

from lsprotocol import types

from lsp_client.client import LSPClientBase


class TyClient(
    LSPClientBase,
):
    language_id: ClassVar = types.LanguageKind.Python
    server_cmd = (
        "ty",
        "lsp",
    )

    # TODO add support for ty
