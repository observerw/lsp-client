"""
Digital-IDE Language Server for Verilog/VHDL - https://nc-ai.cn/en/article/c2mce3m0/
"""

from typing import ClassVar

from lsprotocol import types

from lsp_client.client import LSPClientBase


class DigitalIDEClient(
    LSPClientBase,
):
    # Note: Using generic string for Verilog/VHDL as not available in LanguageKind
    language_id: ClassVar = types.LanguageKind("verilog")
    server_cmd = (
        "digital-ide",
        "--lsp",
    )

    # TODO add support for digital-ide
