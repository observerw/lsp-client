from __future__ import annotations

import anyio

import lsp_client
from lsp_client.clients.rust_analyzer import RustAnalyzerClient, RustAnalyzerLocalServer

lsp_client.enable_logging()


async def main():
    async with RustAnalyzerClient(server=RustAnalyzerLocalServer()) as client:
        print(client.get_language_id())


if __name__ == "__main__":
    anyio.run(main)
