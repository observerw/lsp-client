from __future__ import annotations

import pytest

from lsp_client import LSPClient
from lsp_client.clients import local_clients
from lsp_client.utils.inspect import inspect_capabilities


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "client_cls",
    local_clients,
)
async def test_capabilities_match(client_cls: type[LSPClient]):
    # instantiate the client directly to get its default server
    client = client_cls()
    server = client.server

    mismatches = []
    async for result in inspect_capabilities(server, client_cls):
        if result.client != result.server:
            mismatches.append(
                f"{result.capability}: client={result.client}, server={result.server}"
            )

    if mismatches:
        pytest.fail(
            f"Capability mismatch for {client_cls.__name__}:\n" + "\n".join(mismatches)
        )
