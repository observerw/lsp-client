from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override

from lsp_client.protocol import (
    CapabilityClientProtocol,
    CapabilityProtocol,
    ServerRequestHookProtocol,
)


class WithDenoCacheRequest(
    ServerRequestHookProtocol,
    CapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return ("deno/cache",)
