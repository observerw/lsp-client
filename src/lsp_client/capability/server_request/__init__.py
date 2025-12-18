from __future__ import annotations

from typing import Final

from .show_document_request import WithRespondShowDocumentRequest
from .show_message_request import WithRespondShowMessageRequest
from .workspace_configuration import WithRespondConfigurationRequest
from .workspace_folders import WithRespondWorkspaceFoldersRequest

capabilities: Final = (
    WithRespondConfigurationRequest,
    WithRespondShowDocumentRequest,
    WithRespondShowMessageRequest,
    WithRespondWorkspaceFoldersRequest,
)

__all__ = [
    "WithRespondConfigurationRequest",
    "WithRespondShowDocumentRequest",
    "WithRespondShowMessageRequest",
    "WithRespondWorkspaceFoldersRequest",
]
