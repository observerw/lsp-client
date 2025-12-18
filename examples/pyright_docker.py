from __future__ import annotations

from pathlib import Path

import anyio

from lsp_client import Position
from lsp_client.clients.pyright import PyrightClient, PyrightDockerServer


async def main():
    workspace = Path.cwd()
    async with PyrightClient(
        server=PyrightDockerServer(mounts=[workspace]),
        workspace=workspace,
    ) as client:
        refs = await client.request_definition_locations(
            file_path=__file__,
            position=Position(12, 28),
        )

        if not refs:
            print("No definition locations found.")
            return

        for ref in refs:
            print(f"Definition location found at {ref.uri} - Range: {ref.range}")


if __name__ == "__main__":
    anyio.run(main)
