"""
Github Copilot Language Server - https://www.npmjs.com/package/@github/copilot-language-server
"""

from typing import ClassVar

import lsprotocol.types as types

import lsp_client.capability as cap
from lsp_client.client import LSPClientBase


class CopilotServerClient(
    cap.WithRequestInlineCompletions,
    cap.WithRequestExecuteCommand,
    cap.WithNotifyChangeConfiguration,
    cap.WithNotifyChangeWorkspaceFolders,
    cap.WithReceiveLogMessage,
    cap.WithRespondShowMessage,
    LSPClientBase,
):
    language_id: ClassVar = types.LanguageKind("unknown")
    server_cmd: ClassVar = ("copilot-language-server",)

    # TODO add client capabilities
