from __future__ import annotations

from lsp_client.jsonrpc.channel import RespSender
from lsp_client.jsonrpc.types import RawNotification, RawRequest

type ServerRequest = tuple[RawRequest, RespSender] | RawNotification
