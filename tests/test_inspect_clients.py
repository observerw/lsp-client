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
        # We only care about capabilities that the client CLAIMS to support but the server doesn't,
        # or vice versa (though usually we care more about the client expecting something the server doesn't provide)
        if result.client != result.server:
            mismatches.append(
                f"{result.capability}: client={result.client}, server={result.server}"
            )

    if mismatches:
        # For now, let's just log them or fail if we want strict matching.
        # The user asked to "detect", so failing on mismatch is a good way to ensure they stay in sync.
        # However, some servers might legitimately not support some things that we've implemented in the client (maybe for newer versions).
        # But usually they should match if we are targeting a specific version in the container.
        pytest.fail(
            f"Capability mismatch for {client_cls.__name__}:\n" + "\n".join(mismatches)
        )
