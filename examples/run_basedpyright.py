from __future__ import annotations

import asyncio
from pathlib import Path

from lsp_client import Position, Range
from lsp_client.clients.based_pyright import BasedPyrightClient

repo_path = Path.cwd()
curr_path = Path(__file__)


async def main():
    async with BasedPyrightClient(workspace=repo_path, sync_file=False) as client:
        #      ^________________^
        # found all references of `BasedPyrightClient` class
        symbols = await client.request_document_base_symbols(
            file_path="src/lsp_client/clients/based_pyright.py",
        )
        print(symbols)
        refs = await client.request_references(
            file_path="src/lsp_client/clients/based_pyright.py",
            position=Position(32, 24),
            include_declaration=False,
        )
        assert refs and len(refs) > 0, (
            "No references found for BasedPyrightClient class"
        )
        for ref in refs:
            print(f"Found references: {ref}")

        # check if includes reference in current file
        assert any(
            client.from_uri(ref.uri) == curr_path
            and ref.range == Range(Position(14, 15), Position(14, 33))
            for ref in refs
        )
        print("All references found successfully.")


if __name__ == "__main__":
    asyncio.run(main())
