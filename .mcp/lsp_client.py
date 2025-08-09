from __future__ import annotations

from lsp_client import start_mcp
from lsp_client.clients.based_pyright import BasedPyrightClient

start_mcp(BasedPyrightClient())
