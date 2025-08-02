from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from lsp_client import Position, Range, lsp_type
from lsp_client.clients.based_pyright import BasedPyrightClient

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

repo_path = Path.cwd()
curr_path = Path(__file__)


async def main():
    async with BasedPyrightClient().start(workspace=repo_path) as client:
        # found all references of `BasedPyrightClient` class
        refs = await client.request_references(
            file_path="src/lsp_client/clients/based_pyright.py",
            position=Position(40, 24),
        )
        assert refs and len(refs) > 0, (
            "No references found for BasedPyrightClient class"
        )
        for ref in refs:
            print(f"Found references: {ref}")

        # check if includes reference in current file
        assert any(
            client.from_uri(ref.uri) == curr_path
            and ref.range == Range(Position(21, 15), Position(21, 33))
            for ref in refs
        )
        print("All references found successfully.")

        # find the definition of `main` function
        def_task = client.create_request(
            client.request_definition(
                file_path=curr_path,
                position=Position(58, 8),
            )
        )

    match def_task.result():
        case [lsp_type.Location() as loc]:
            print(f"Found definition: {loc}")
            assert client.from_uri(loc.uri) == curr_path
            assert loc.range == Range(Position(20, 10), Position(20, 14))
    print("Definition found successfully.")


if __name__ == "__main__":
    asyncio.run(main())
