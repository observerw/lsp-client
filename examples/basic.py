from pathlib import Path

from asyncio_addon import async_main

from lsp_client import Position, Range, RelPath, lsp_type
from lsp_client.servers.based_pyright import BasedPyrightClient

repo_path = Path.cwd()


@async_main
async def main():
    async with BasedPyrightClient.start(repo_path=repo_path) as client:
        if refs := await client.request_references(
            file_path="src/lsp_client/servers/based_pyright.py",
            position=Position(10, 24),
        ):
            assert any(
                client.from_uri(ref.uri).relative_to(repo_path)
                == RelPath("examples/basic.py")
                and ref.range == Range(Position(10, 15), Position(10, 33))
                for ref in refs
            )

        def_task = client.create_request(
            client.request_definition(
                file_path="examples/basic.py",
                position=Position(42, 16),
            )
        )

    match def_task.result():
        case [lsp_type.Location() as loc]:
            assert client.from_uri(loc.uri).relative_to(repo_path) == RelPath(
                "examples/basic.py"
            )
            assert loc.range == Range(Position(9, 10), Position(9, 14))


if __name__ == "__main__":
    main()
