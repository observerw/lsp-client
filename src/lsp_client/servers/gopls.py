"""
gopls Language Server for Go - https://github.com/golang/tools/tree/master/gopls
"""

from typing import ClassVar

from lsprotocol import types

from lsp_client.client import LSPClientBase


class GoplsClient(
    LSPClientBase,
):
    language_id: ClassVar = types.LanguageKind.Go
    server_cmd = (
        "gopls",
    )

    # TODO add support for gopls
