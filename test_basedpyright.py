from __future__ import annotations

import asyncio as aio

from loguru import logger

from lsp_client.clients.based_pyright import BasedPyrightClient

logger.enable("lsp_client")


async def main():
    async with BasedPyrightClient().start(workspace=".") as client:
        symbols = await client.request_workspace_symbol_information("next_server")
        print(symbols)


if __name__ == "__main__":
    aio.run(main())
