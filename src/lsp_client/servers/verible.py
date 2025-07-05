"""
Verible Language Server for SystemVerilog - https://github.com/chipsalliance/verible
"""

from typing import ClassVar

from lsprotocol import types

from lsp_client.client import LSPClientBase


class VeribleClient(
    LSPClientBase,
):
    # Note: Using generic string for SystemVerilog as not available in LanguageKind
    language_id: ClassVar = types.LanguageKind("systemverilog")
    server_cmd = (
        "verible-verilog-ls",
    )

    # TODO add support for verible
