"""Re-export some lsp types for convenience."""
from __future__ import annotations

import os

from lsprotocol import types

Position = types.Position
Range = types.Range

AnyPath = str | os.PathLike
