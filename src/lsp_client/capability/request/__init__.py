from __future__ import annotations

from typing import Final

from .call_hierarchy import WithRequestCallHierarchy
from .declaration import WithRequestDeclaration
from .definition import WithRequestDefinition
from .document_symbol import WithRequestDocumentSymbol
from .hover import WithRequestHover
from .implementation import WithRequestImplementation
from .inline_value import WithRequestInlineValue
from .reference import WithRequestReferences
from .signature_help import WithRequestSignatureHelp
from .type_definition import WithRequestTypeDefinition
from .type_hierarchy import WithRequestTypeHierarchy
from .workspace_symbol import WithRequestWorkspaceSymbol

capabilities: Final = (
    WithRequestCallHierarchy,
    WithRequestDeclaration,
    WithRequestDefinition,
    WithRequestDocumentSymbol,
    WithRequestHover,
    WithRequestImplementation,
    WithRequestInlineValue,
    WithRequestReferences,
    WithRequestSignatureHelp,
    WithRequestTypeDefinition,
    WithRequestTypeHierarchy,
    WithRequestWorkspaceSymbol,
)

__all__ = [
    "WithRequestCallHierarchy",
    "WithRequestDeclaration",
    "WithRequestDefinition",
    "WithRequestDocumentSymbol",
    "WithRequestHover",
    "WithRequestImplementation",
    "WithRequestInlineValue",
    "WithRequestReferences",
    "WithRequestSignatureHelp",
    "WithRequestTypeDefinition",
    "WithRequestTypeHierarchy",
    "WithRequestWorkspaceSymbol",
    "capabilities",
]
