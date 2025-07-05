"""
Csharp Language Server For C# - https://github.com/SofusA/csharp-language-server
"""

from typing import ClassVar

from lsprotocol import types

from lsp_client.client import LSPClientBase


class CsharpLanguageServerClient(
    LSPClientBase,
):
    language_id: ClassVar = types.LanguageKind.CSharp
    server_cmd = (
        "csharp-language-server",
    )

    # TODO add support for csharp-language-server
