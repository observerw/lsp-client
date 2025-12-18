from __future__ import annotations

from typing import Protocol, runtime_checkable

from lsp_client import LSPClient
from lsp_client.capability.request import (
    WithRequestCallHierarchy,
    WithRequestDefinition,
    WithRequestDocumentSymbol,
    WithRequestReferences,
)


@runtime_checkable
class ExpectClientProtocol(
    WithRequestReferences,
    WithRequestDefinition,
    Protocol,
):
    """We expect the client to (at least) support 'references' and 'definition' requests."""


class BadClient(
    LSPClient,
    WithRequestDocumentSymbol,
):
    """The bad client does not meet our expectations."""


class GoodClient(
    LSPClient,
    WithRequestReferences,
    WithRequestDefinition,
    WithRequestCallHierarchy,
):
    """The good client meets our expectations."""


assert not issubclass(BadClient, ExpectClientProtocol)
assert issubclass(GoodClient, ExpectClientProtocol)
