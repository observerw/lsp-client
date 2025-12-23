from __future__ import annotations

import shutil
import subprocess

import pytest

from lsp_client.clients import clients
from lsp_client.utils.inspect import inspect_capabilities


def has_docker() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        subprocess.run(["docker", "info"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


@pytest.mark.skipif(not has_docker(), reason="Docker not available")
@pytest.mark.asyncio
@pytest.mark.parametrize("client_cls", clients)
async def test_client_capabilities_match_container(client_cls):
    client = client_cls()
    servers = client.create_default_servers()
    server = servers.container

    if server is None:
        pytest.skip(f"No container server defined for {client_cls.__name__}")

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
