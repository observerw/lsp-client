"""
TypeScript Language Server - https://github.com/typescript-language-server/typescript-language-server
"""

from typing import ClassVar

from lsprotocol import types

from lsp_client.client import LSPClientBase


class TypeScriptLanguageServerClient(
    LSPClientBase,
):
    language_id: ClassVar = types.LanguageKind.TypeScript
    server_cmd = (
        "typescript-language-server",
        "--stdio",
    )

    # TODO add support for typescript-language-server
