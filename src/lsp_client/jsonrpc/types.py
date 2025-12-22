from __future__ import annotations

from typing import Any, TypedDict

from .id import ID

# --------------------------------- base type -------------------------------- #

type RawParams = list[Any] | dict[str, Any]

# --------------------------------- raw type --------------------------------- #


class RawRequest(TypedDict):
    id: ID | None
    method: str
    params: RawParams | None
    jsonrpc: str


class RawNotification(TypedDict):
    method: str
    params: RawParams | None
    jsonrpc: str


class RawError(TypedDict):
    id: ID | None
    error: dict[str, Any] | None
    jsonrpc: str


class RawResponse(TypedDict):
    id: ID | None
    result: Any | None
    jsonrpc: str


# -------------------------------- package type ------------------------------- #


type RawRequestPackage = RawRequest | RawNotification
type RawResponsePackage = RawResponse | RawError
type RawPackage = RawRequestPackage | RawResponsePackage
