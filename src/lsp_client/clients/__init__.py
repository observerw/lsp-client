from __future__ import annotations

from .deno import DenoClient
from .pyrefly import PyreflyClient
from .pyright import PyrightClient
from .rust_analyzer import RustAnalyzerClient
from .typescript import TypescriptClient

PythonClient = PyrightClient
RustClient = RustAnalyzerClient
TypeScriptClient = TypescriptClient
DenoLSPClient = DenoClient

__all__ = [
    "DenoLSPClient",
    "PyreflyClient",
    "PythonClient",
    "RustClient",
    "TypeScriptClient",
]
