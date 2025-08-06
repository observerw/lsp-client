from __future__ import annotations

from uuid import uuid4

from lsp_client import jsonrpc


def jsonrpc_uuid() -> jsonrpc.ID:
    return uuid4().hex
