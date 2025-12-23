from __future__ import annotations

from typing import Final

from .deno import DenoClient
from .gopls import GoplsClient
from .pyrefly import PyreflyClient
from .pyright import PyrightClient
from .rust_analyzer import RustAnalyzerClient
from .typescript import TypescriptClient

GoClient = GoplsClient
PythonClient = PyrightClient
RustClient = RustAnalyzerClient
TypeScriptClient = TypescriptClient

clients: Final = (
    GoplsClient,
    PyreflyClient,
    PyrightClient,
    RustAnalyzerClient,
    DenoClient,
    TypescriptClient,
)

__all__ = [
    "DenoClient",
    "GoClient",
    "GoplsClient",
    "PyreflyClient",
    "PythonClient",
    "RustClient",
    "TypeScriptClient",
    "client",
]
