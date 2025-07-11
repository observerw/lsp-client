from __future__ import annotations

import json
from typing import Any, Protocol, TypedDict, runtime_checkable

from lsprotocol import converters, types

type JsonRpcID = str | int
type JsonRpcRawParams = list[Any] | dict[str, Any]


class JsonRpcRawRequest(TypedDict):
    id: JsonRpcID | None
    method: str
    params: JsonRpcRawParams | None
    jsonrpc: str


class JsonRpcRawNotification(TypedDict):
    method: str
    params: JsonRpcRawParams | None
    jsonrpc: str


class JsonRpcRawError(TypedDict):
    id: JsonRpcID | None
    error: dict[str, Any] | None
    jsonrpc: str


class JsonRpcRawResponse(TypedDict):
    id: JsonRpcID | None
    result: Any | None
    jsonrpc: str


type JsonRpcRawReqPackage = JsonRpcRawRequest | JsonRpcRawNotification
type JsonRpcRawRespPackage = JsonRpcRawResponse | JsonRpcRawError
type JsonRpcRawPackage = JsonRpcRawReqPackage | JsonRpcRawRespPackage


@runtime_checkable
class JsonRpcResponse[T](Protocol):
    """
    Duck-type schema for extracting the result type from `lsprotocol` Response schema.

    e.g.

    ```python
    def result[T](self, resp: JsonRpcResponse[T]) -> T:
        return resp.result
    ```
    """

    result: T


lsp_converter = converters.get_converter()


def package_serialize(package: JsonRpcRawPackage, *, cache: bool = False) -> str:
    cache_key = f"_cache_{id(package)}"
    if cached := package_serialize.__dict__.get(cache_key):
        assert isinstance(cached, str)
        return cached

    serialized = json.dumps(package, sort_keys=True)  # stable serialization
    if cache:
        package_serialize.__dict__[cache_key] = serialized

    return serialized


def response_deserialize[R](
    raw_resp: JsonRpcRawRespPackage,
    schema: type[JsonRpcResponse[R]],
) -> R:
    match raw_resp:
        case {"error": _} as raw_err_resp:
            err_resp = lsp_converter.structure(raw_err_resp, types.ResponseErrorMessage)
            raise (
                ValueError(f"JSON-RPC Error {err.code}: {err.message}")
                if (err := err_resp.error)
                else ValueError(f"JSON-RPC Error: {err_resp}")
            )
        case {"result": _} as raw_resp:
            resp = lsp_converter.structure(raw_resp, schema)
            return resp.result
        case unexpected:
            raise ValueError(f"Unexpected JSON-RPC response: {unexpected}")
