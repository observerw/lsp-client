from typing import ClassVar

from lsprotocol import types

from lsp_client.client import LSPClientBase


class RuffClient(
    LSPClientBase,
):
    language_id: ClassVar = types.LanguageKind.Python
    server_cmd = (
        "ruff",
        "server",
    )

    # TODO add support for ruff
