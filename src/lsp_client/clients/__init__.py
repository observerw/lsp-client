from __future__ import annotations

from .pyrefly import PyreflyClient
from .pyright import PyrightClient
from .rust_analyzer import RustAnalyzerClient
from .typescript import TypescriptClient

PythonClient = PyrightClient
RustClient = RustAnalyzerClient
TypeScriptClient = TypescriptClient

__all__ = [
    "PyreflyClient",
    "PythonClient",
    "RustClient",
    "TypeScriptClient",
]
