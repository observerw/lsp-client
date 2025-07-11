"""
Example of how to declare a client protocol that requires client to implement certain capabilities.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from lsp_client import LSPClientBase, lsp_cap


class GoodClient(
    lsp_cap.WithRequestReferences,
    lsp_cap.WithRequestDefinitionLink,
    LSPClientBase,
): ...


class BadClient(
    lsp_cap.WithRequestCompletions,
    LSPClientBase,
): ...


@runtime_checkable
class DesiredClientProtocol(
    lsp_cap.WithRequestReferences,
    lsp_cap.WithRequestDefinitionLink,
    Protocol,
): ...


good: type[DesiredClientProtocol] = GoodClient
# type[BadClient]  is not assignable to type[DesiredClientProtocol]
bad: type[DesiredClientProtocol] = BadClient  # type: ignore[assignment]
