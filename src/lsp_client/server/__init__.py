from __future__ import annotations

from attrs import frozen

from .abc import Server
from .container import ContainerServer
from .exception import ServerError, ServerInstallationError, ServerRuntimeError
from .local import LocalServer


@frozen
class DefaultServers:
    local: LocalServer
    container: ContainerServer


__all__ = [
    "ContainerServer",
    "DefaultServers",
    "LocalServer",
    "Server",
    "ServerError",
    "ServerInstallationError",
    "ServerRuntimeError",
]
