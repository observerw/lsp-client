"""
clangd Language Server for C/C++/Objective-C - https://github.com/clangd/clangd
"""

from typing import ClassVar

from lsprotocol import types

from lsp_client.client import LSPClientBase


class ClangdClient(
    LSPClientBase,
):
    language_id: ClassVar = types.LanguageKind.Cpp
    server_cmd = (
        "clangd",
    )

    # TODO add support for clangd
