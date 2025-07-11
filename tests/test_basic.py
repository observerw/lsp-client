from __future__ import annotations

import asyncio as aio
import logging

from lsp_client import Position
from lsp_client.servers.based_pyright import BasedPyrightClient

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def main():
    async with BasedPyrightClient.start(
        repo_path=".",
        server_count=4,
        pending_timeout=5.0,
    ) as client:
        refs = await client.request_references(
            file_path="src/lsp_client/capability.py",
            position=Position(16, 25),
        )
    if not refs:
        print("No references found.")
        return

    for ref in refs:
        print(ref)


if __name__ == "__main__":
    aio.run(main())
