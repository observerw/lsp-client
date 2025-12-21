from __future__ import annotations

import os


def disable_auto_installation() -> bool:
    return os.getenv("LSP_CLIENT_DISABLE_AUTO_INSTALLATION") is not None
