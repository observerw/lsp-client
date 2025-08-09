from __future__ import annotations

from typing import Protocol

from lsp_client import lsp_cap


class MCPClientProtocol(
    lsp_cap.WithRequestDocumentSymbols,
    lsp_cap.LSPCapabilityClientProtocol,
    Protocol,
): ...
