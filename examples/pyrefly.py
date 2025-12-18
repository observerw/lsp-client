# Example: Using Pyrefly LSP server for Python reference finding
#
# This example demonstrates how to use the Pyrefly language server
# to find all references to a symbol in Python code. Pyrefly is a
# Python language server that provides enhanced static analysis.

from __future__ import annotations

import anyio

import lsp_client
from lsp_client import Position, Range
from lsp_client.clients.pyrefly import PyreflyClient, PyreflyLocalServer

lsp_client.enable_logging()


async def main():
    # Initialize Pyrefly client with local server
    async with PyreflyClient(server=PyreflyLocalServer()) as client:
        # Request references to PyreflyClient at line 21, column 19
        refs = await client.request_references(
            file_path="src/lsp_client/clients/pyrefly.py",
            position=Position(21, 19),
            include_declaration=False,  # Don't include the declaration itself
        )

        if not refs:
            print("No references found.")
            return

        # Print all found references
        for ref in refs:
            print(f"Reference found at {ref.uri} - Range: {ref.range}")

        # Verify that this example file contains a reference to PyreflyClient
        # This demonstrates the reference finding functionality works correctly
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
    anyio.run(main)  # Run the async example
