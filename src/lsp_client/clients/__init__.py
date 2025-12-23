from __future__ import annotations

from .gopls import GoplsClient
from .pyrefly import PyreflyClient
from .pyright import PyrightClient
from .rust_analyzer import RustAnalyzerClient
from .typescript import TypescriptClient

GoClient = GoplsClient
PythonClient = PyrightClient
RustClient = RustAnalyzerClient
TypeScriptClient = TypescriptClient

__all__ = [
    "GoClient",
    "GoplsClient",
    "PyreflyClient",
    "PythonClient",
    "RustClient",
    "TypeScriptClient",
]
