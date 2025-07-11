from __future__ import annotations

from uuid import uuid4

from lsp_client.jsonrpc import JsonRpcID


def jsonrpc_uuid() -> JsonRpcID:
    return uuid4().hex
