from __future__ import annotations

from .deno import DenoClient
from .pyrefly import PyreflyClient
from .pyright import PyrightClient
from .rust_analyzer import RustAnalyzerClient
from .ty import TyClient
from .typescript import TypescriptClient

PythonClient = PyrightClient
RustClient = RustAnalyzerClient
TypeScriptClient = TypescriptClient
DenoLSPClient = DenoClient
TyLSPClient = TyClient

__all__ = [
    "DenoLSPClient",
    "PyreflyClient",
    "PythonClient",
    "RustClient",
    "TyLSPClient",
    "TypeScriptClient",
]
