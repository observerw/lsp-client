from __future__ import annotations

from typing import Final

from .did_change_configuration import WithNotifyDidChangeConfiguration
from .text_document_synchronize import WithNotifyTextDocumentSynchronize

capabilities: Final = (
    WithNotifyDidChangeConfiguration,
    WithNotifyTextDocumentSynchronize,
)

__all__ = [
    "WithNotifyDidChangeConfiguration",
    "WithNotifyTextDocumentSynchronize",
    "capabilities",
]
