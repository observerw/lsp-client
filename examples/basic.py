from __future__ import annotations

from pathlib import Path

from asyncio_addon import async_main

from lsp_client import Position, Range, lsp_type
from lsp_client.servers.based_pyright import BasedPyrightClient

repo_path = Path.cwd()
curr_path = Path(__file__)


@async_main
async def main():
    async with BasedPyrightClient.start(repo_path=repo_path) as client:
        # found all references of `BasedPyrightClient` class
        if refs := await client.request_references(
            file_path="src/lsp_client/servers/based_pyright.py",
            position=Position(14, 24),
        ):
            for ref in refs:
                print(f"Found references: {ref}")

            # check if includes reference in current file
            assert any(
                client.from_uri(ref.uri) == curr_path
                and ref.range == Range(Position(15, 15), Position(15, 33))
                for ref in refs
            )
            print("All references found successfully.")

        # find the definition of `main` function
        def_task = client.create_request(
            client.request_definition(
                file_path=curr_path,
                position=Position(49, 8),
            )
        )

    match def_task.result():
        case [lsp_type.Location() as loc]:
            print(f"Found definition: {loc}")
            assert client.from_uri(loc.uri) == curr_path
            assert loc.range == Range(Position(14, 10), Position(14, 14))
    print("Definition found successfully.")


if __name__ == "__main__":
    main()
