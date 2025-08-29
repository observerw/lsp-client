from __future__ import annotations

import asyncio

from lsp_client import Position, logger
from lsp_client.clients.ty import TyClient

logger.enable("lsp_client")


async def main():
    async with TyClient(workspace=".") as client:
        refs = await client.request_references(
            file_path="examples/run_ty.py",
            position=Position(11, 23),
            include_declaration=False,
        )
        print(refs)


if __name__ == "__main__":
    asyncio.run(main())
