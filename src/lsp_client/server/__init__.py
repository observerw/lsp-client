from __future__ import annotations

from attrs import frozen

from .abc import Server
from .container import ContainerServer
from .exception import ServerRuntimeError
from .local import LocalServer


@frozen
class DefaultServers:
    local: LocalServer
    container: ContainerServer


__all__ = [
    "ContainerServer",
    "DefaultServers",
    "LSPServer",
    "LocalServer",
    "Server",
    "ServerRuntimeError",
]
