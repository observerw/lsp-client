from __future__ import annotations

import asyncio as aio

from lsp_client import Position, logger
from lsp_client.clients.ty import TyClient, TyConfig

logger.enable("lsp_client")


async def main():
    async with TyClient(
        config=TyConfig(
            diagnostic_mode="workspace",
        )
    ).start(workspace=".") as client:
        refs = await client.request_references(
            file_path="examples/test_ty.py",
            position=Position(9, 23),
            include_declaration=False,
        )
        print(refs)


if __name__ == "__main__":
    aio.run(main())
