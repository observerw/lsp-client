from __future__ import annotations

from .abc import Server


class ServerRuntimeError(RuntimeError):
    def __init__(self, server: Server, *args: object):
        super().__init__(*args)
        self.server = server
