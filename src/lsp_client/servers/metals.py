"""
Metals Language Server for Scala - https://github.com/scalameta/metals
"""

from typing import ClassVar

from lsprotocol import types

from lsp_client.client import LSPClientBase


class MetalsClient(
    LSPClientBase,
):
    language_id: ClassVar = types.LanguageKind.Scala
    server_cmd = (
        "metals",
    )

    # TODO add support for metals
