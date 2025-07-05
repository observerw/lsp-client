"""
rust-analyzer Language Server for Rust - https://github.com/rust-lang/rust-analyzer
"""

from typing import ClassVar

from lsprotocol import types

from lsp_client.client import LSPClientBase


class RustAnalyzerClient(
    LSPClientBase,
):
    language_id: ClassVar = types.LanguageKind.Rust
    server_cmd = (
        "rust-analyzer",
    )

    # TODO add support for rust-analyzer
