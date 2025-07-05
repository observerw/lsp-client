import asyncio as aio

from lsp_client.jsonrpc import JsonRpcRawReqPackage

ServerRequestQueue = aio.Queue[JsonRpcRawReqPackage]
