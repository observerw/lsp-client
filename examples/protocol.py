# Example: Protocol-based capability checking for LSP clients
#
# This example demonstrates how to use Python's Protocol to define expected
# capabilities for LSP clients and perform runtime checks to ensure clients
# meet those requirements.

from __future__ import annotations

from typing import Protocol, runtime_checkable

from lsp_client import Client
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
    """Protocol defining minimum expected client capabilities.

    This protocol specifies that any client implementing it must support
    both 'references' and 'definition' LSP requests. Using @runtime_checkable
    allows us to use isinstance() and issubclass() checks at runtime.
    """


class BadClient(
    Client,
    WithRequestDocumentSymbol,
):
    """Client that fails to meet protocol requirements.

    This client only implements document symbol capability but lacks
    the required references and definition capabilities, making it
    incompatible with ExpectClientProtocol.
    """


class GoodClient(
    Client,
    WithRequestReferences,
    WithRequestDefinition,
    WithRequestCallHierarchy,
):
    """Client that satisfies protocol requirements.

    This client implements both required capabilities (references and
    definition) plus an additional capability (call hierarchy), making
    it fully compatible with ExpectClientProtocol.
    """


# Runtime checks to verify protocol compliance
assert not issubclass(
    BadClient, ExpectClientProtocol
)  # Should fail - missing required capabilities
assert issubclass(
    GoodClient, ExpectClientProtocol
)  # Should pass - meets all requirements
