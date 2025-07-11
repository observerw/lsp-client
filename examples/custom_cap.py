"""
Example of how to implement a custom capability in an LSP client.
"""
from __future__ import annotations

import logging
from typing import override

from lsprotocol import types

from lsp_client import lsp_cap
from lsp_client.servers.based_pyright import BasedPyrightClient

logger = logging.getLogger(__name__)


# Custom capability to handle log messages with a fancy log message handler
class WithFancyReceiveLogMessage(lsp_cap.WithReceiveLogMessage):
    @override
    async def receive_log_message(self, req: types.LogMessageNotification):
        logger.info(
            "✨ This is a fancy log message handler! ✨: %s",
            req.params.message,
        )


class MyLSPServerClient(
    WithFancyReceiveLogMessage,
    BasedPyrightClient,
): ...
