from __future__ import annotations

from typing import Final

from .deno import DenoClient
from .pyrefly import PyreflyClient
from .pyright import PyrightClient
from .rust_analyzer import RustAnalyzerClient
from .tsserver import TsserverClient

clients: Final = (
    DenoClient,
    PyreflyClient,
    PyrightClient,
    RustAnalyzerClient,
    TsserverClient,
)

PythonClient = PyrightClient
RustClient = RustAnalyzerClient
TypeScriptClient = DenoClient

__all__ = [
    "PythonClient",
    "RustClient",
    "TypeScriptClient",
    "clients",
]
