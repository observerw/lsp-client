from __future__ import annotations

from lsp_client import jsonrpc

type ServerRequest = (
    tuple[jsonrpc.RawRequest, jsonrpc.RespSender] | jsonrpc.RawNotification
)
