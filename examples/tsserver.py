# Example: Using TypeScript Language Server for TypeScript code analysis
#
# This example demonstrates how to use the TypeScript Language Server
# to find definition locations in TypeScript code. The typescript-language-server
# provides powerful static analysis for TypeScript and JavaScript projects.

from __future__ import annotations

from pathlib import Path

import anyio

from lsp_client.clients.tsserver import TsserverClient, TsserverLocalServer


async def main():
    # Set up workspace directory
    workspace = Path.cwd()
    async with TsserverClient(
        server=TsserverLocalServer(),
        workspace=workspace,
    ) as client:
        # Example: Find definition of TsserverClient at line 13, column 28
        # This demonstrates the definition lookup capability
        print(f"Using language server for: {client.get_language_id()}")

        # In a real scenario, you would provide a TypeScript file path
        # refs = await client.request_definition_locations(
        #     file_path="src/index.ts",
        #     position=Position(10, 15),
        # )
        #
        # if not refs:
        #     print("No definition locations found.")
        #     return
        #
        # # Display all definition locations found
        # for ref in refs:
        #     print(f"Definition location found at {ref.uri} - Range: {ref.range}")


if __name__ == "__main__":
    anyio.run(main)  # Run the async example
