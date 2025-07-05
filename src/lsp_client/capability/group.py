from typing import Protocol, runtime_checkable

from .request import (
    WithRequestCompletions,
    WithRequestDefinition,
    WithRequestDocumentSymbols,
    WithRequestHover,
    WithRequestInlineCompletions,
    WithRequestReferences,
    WithRequestWorkspaceSymbols,
)


@runtime_checkable
class WithBasicCapabilities(
    WithRequestReferences,
    WithRequestDefinition,
    WithRequestDocumentSymbols,
    WithRequestWorkspaceSymbols,
    WithRequestCompletions,
    WithRequestInlineCompletions,
    WithRequestHover,
    Protocol,
):
    """Common capabilities that a full-featured LSP server should implement."""
