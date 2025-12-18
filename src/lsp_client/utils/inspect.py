from __future__ import annotations

import itertools

from attrs import frozen

from lsp_client.capability.notification import capabilities as notification_capabilities
from lsp_client.capability.request import capabilities as request_capabilities
from lsp_client.capability.server_notification import (
    capabilities as server_notification_capabilities,
)
from lsp_client.capability.server_request import (
    capabilities as server_request_capabilities,
)
from lsp_client.client.abc import LSPClient
from lsp_client.jsonrpc.convert import lsp_type, request_serialize, response_deserialize
from lsp_client.server.abc import LSPServer


@frozen
class CheckResult:
    capability: str
    client: bool
    server: bool


async def inspect_capabilities(server: LSPServer, client_cls: type[LSPClient]):
    if not __debug__:
        raise RuntimeError("inspect_capabilities can only be used in debug mode")

    async with server.serve():
        req = lsp_type.InitializeRequest(
            id="initialize",
            params=lsp_type.InitializeParams(
                capabilities=lsp_type.ClientCapabilities()
            ),
        )
        resp = await server.request(request_serialize(req))
        resp = response_deserialize(resp, lsp_type.InitializeResponse)
        await server.kill()

    server_capabilities = resp.capabilities
    server_info = resp.server_info

    for cap in itertools.chain(
        request_capabilities,
        notification_capabilities,
        server_request_capabilities,
        server_notification_capabilities,
    ):
        client_available = issubclass(client_cls, cap)

        try:
            cap.check_server_capability(server_capabilities, server_info)
            server_available = True
        except AssertionError:
            server_available = False

        for method in cap.methods():
            yield CheckResult(
                capability=method,
                client=client_available,
                server=server_available,
            )
