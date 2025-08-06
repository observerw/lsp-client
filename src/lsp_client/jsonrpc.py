"""All JSON-RPC related types and data structures"""

from __future__ import annotations

import json
from typing import Any, TypedDict, cast

from lsprotocol import converters, types

from lsp_client.channel import (
    ManyShotReceiver,
    ManyShotSender,
    OneShotReceiver,
    OneShotSender,
    Receiver,
    Sender,
    ShotTable,
    channel,
    manyshot_channel,
    oneshot_channel,
)
from lsp_client.types import Notification, Request, Response

# --------------------------------- base type -------------------------------- #

type ID = str | int
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


type RawRequestPackage = RawRequest | RawNotification
type RawResponsePackage = RawResponse | RawError
type RawPackage = RawRequestPackage | RawResponsePackage

# ------------------------------ converter utils ----------------------------- #

converter = converters.get_converter()


def package_serialize(package: RawPackage, *, cache: bool = False) -> str:
    cache_key = f"_cache_{id(package)}"
    if cached := package_serialize.__dict__.get(cache_key):
        assert isinstance(cached, str)
        return cached

    serialized = json.dumps(package, sort_keys=True)  # stable serialization
    if cache:
        package_serialize.__dict__[cache_key] = serialized

    return serialized


def request_deserialize[R](raw_req: RawRequestPackage, schema: type[R]) -> R:
    return converter.structure(raw_req, schema)


def request_serialize(request: Request) -> RawRequest:
    return cast(RawRequest, converter.unstructure(request))


def notification_serialize(notification: Notification) -> RawNotification:
    return cast(RawNotification, converter.unstructure(notification))


def response_deserialize[R](
    raw_resp: RawResponsePackage, schema: type[Response[R]]
) -> R:
    """Deserialize a JSON-RPC response package. raise `ValueError` if the response is an error."""

    match raw_resp:
        case {"error": _} as raw_err_resp:
            err_resp = converter.structure(raw_err_resp, types.ResponseErrorMessage)
            raise (
                ValueError(f"JSON-RPC Error {err.code}: {err.message}")
                if (err := err_resp.error)
                else ValueError(f"JSON-RPC Error: {err_resp}")
            )
        case {"result": _} as raw_resp:
            resp = converter.structure(raw_resp, schema)
            return resp.result
        case unexpected:
            raise ValueError(f"Unexpected response: {unexpected}")


def response_serialize(response: Response[Any]) -> RawResponsePackage:
    return cast(RawResponsePackage, converter.unstructure(response))


# ---------------------------------- channel --------------------------------- #

# one shot channel for response to request
type ChannelResponse = RawResponsePackage

response_channel = oneshot_channel[ChannelResponse]
type RespSender = OneShotSender[ChannelResponse]
type RespReceiver = OneShotReceiver[ChannelResponse]

# one shot channel for multiple response
many_response_channel = manyshot_channel[ChannelResponse]
type ManyRespSender = ManyShotSender[ChannelResponse]
type ManyRespReceiver = ManyShotReceiver[ChannelResponse]

# table for response dispatch
ResponseTable = ShotTable[ChannelResponse]

# mpsc channel for sending request
type ChannelRequest = tuple[RawRequest, RespSender | ManyRespSender] | RawNotification

request_channel = channel[ChannelRequest]
type ReqSender = Sender[ChannelRequest]
type ReqReceiver = Receiver[ChannelRequest]
