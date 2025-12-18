from __future__ import annotations

import anyio

import lsp_client
from lsp_client import Position, Range
from lsp_client.clients.pyrefly import PyreflyClient, PyreflyLocalServer

lsp_client.enable_logging()


async def main():
    async with PyreflyClient(server=PyreflyLocalServer()) as client:
        refs = await client.request_references(
            file_path="src/lsp_client/clients/pyrefly.py",
            position=Position(21, 19),
            include_declaration=False,
        )

        if not refs:
            print("No references found.")
            return

        for ref in refs:
            print(f"Reference found at {ref.uri} - Range: {ref.range}")

        assert any(
            ref.uri.endswith(__file__)
            and ref.range
            == Range(
                start=Position(12, 15),
                end=Position(12, 28),
            )
            for ref in refs
        )
        print("Reference assertion passed.")


if __name__ == "__main__":
    anyio.run(main)
