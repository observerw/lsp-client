from __future__ import annotations

from typing import Final

from .pyrefly import PyreflyClient
from .pyright import PyrightClient
from .rust_analyzer import RustAnalyzerClient
from .typescript import TypescriptClient

local_clients: Final = (
    PyrightClient,
    RustAnalyzerClient,
    PyreflyClient,
    TypescriptClient,
)

PythonClient = PyrightClient
RustClient = RustAnalyzerClient
TypeScriptClient = TypescriptClient

__all__ = [
    "PythonClient",
    "RustClient",
    "TypeScriptClient",
    "local_clients",
]
