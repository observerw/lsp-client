from __future__ import annotations

from uuid import uuid4

type ID = str | int


def jsonrpc_uuid() -> ID:
    return uuid4().hex
