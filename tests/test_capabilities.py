# from __future__ import annotations

# import shutil
# import subprocess

# import pytest

# from lsp_client import LSPClient
# from lsp_client.clients import (
#     PyreflyClient,
#     PyrightClient,
#     RustAnalyzerClient,
#     TypescriptClient,
# )
# from lsp_client.server.container import ContainerServer
# from lsp_client.utils.inspect import inspect_capabilities


# def has_docker() -> bool:
#     if not shutil.which("docker"):
#         return False
#     try:
#         subprocess.run(["docker", "info"], check=True, capture_output=True)
#         return True
#     except subprocess.CalledProcessError:
#         return False


# @pytest.mark.skipif(not has_docker(), reason="Docker not available")
# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "client_cls,image",
#     [
#         (PyrightClient, "ghcr.io/observerw/lsp-client/pyright:latest"),
#         (RustAnalyzerClient, "ghcr.io/observerw/lsp-client/rust-analyzer:latest"),
#         (TypescriptClient, "ghcr.io/observerw/lsp-client/typescript:latest"),
#         (PyreflyClient, "ghcr.io/observerw/lsp-client/pyrefly:latest"),
#     ],
# )
# async def test_capabilities_match(client_cls: type[LSPClient], image: str):
#     # Use ContainerServer for testing to ensure environment consistency
#     server = ContainerServer(image=image, mounts=[])

#     mismatches = []
#     async for result in inspect_capabilities(server, client_cls):
#         if result.client != result.server:
#             mismatches.append(
#                 f"{result.capability}: client={result.client}, server={result.server}"
#             )

#     if mismatches:
#         pytest.fail(
#             f"Capability mismatch for {client_cls.__name__} in container {image}:\n"
#             + "\n".join(mismatches)
#         )
