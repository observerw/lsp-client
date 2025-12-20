from __future__ import annotations

from typing import Final

from .log_message import WithReceiveLogMessage
from .log_trace import WithReceiveLogTrace
from .publish_diagnostics import WithReceivePublishDiagnostics
from .show_message import WithReceiveShowMessage

capabilities: Final = (
    WithReceiveLogMessage,
    WithReceiveLogTrace,
    WithReceivePublishDiagnostics,
    WithReceiveShowMessage,
)

__all__ = [
    "WithReceiveLogMessage",
    "WithReceiveLogTrace",
    "WithReceivePublishDiagnostics",
    "WithReceiveShowMessage",
    "capabilities",
]
