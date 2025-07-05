"""
pyrefly Language Server for Python - https://github.com/facebook/pyrefly
"""

from typing import ClassVar

from lsprotocol import types

from lsp_client.client import LSPClientBase


class PyreflyClient(
    LSPClientBase,
):
    language_id: ClassVar = types.LanguageKind.Python
    server_cmd = (
        "pyrefly",
        "lsp-server",
    )

    # TODO add support for pyrefly
