"""Full-featured, well-typed, and easy-to-use LSP client library.

This package provides a comprehensive implementation of the Language Server Protocol (LSP)
for building Python clients and servers. It offers:

- **LSPClient**: Abstract base class for implementing LSP clients
- **LSPServer**: Abstract base class for implementing LSP servers
- **Capability-based protocol**: Clean separation of LSP capabilities
- **Type-safe implementation**: Full type annotations using lsprotocol
- **Async/await support**: Modern Python async patterns
- **Multiple server backends**: Docker, local process, and custom implementations

Example:
    ```python
    import anyio
    from lsp_client.clients.pyrefly import PyreflyClient, PyreflyLocalServer
    from lsp_client import Position

    async def main():
        async with PyreflyClient(server=PyreflyLocalServer()) as client:
            refs = await client.request_references(
                file_path="src/main.py",
                position=Position(21, 19),
                include_declaration=False,
            )
            for ref in refs:
                print(f"Reference found at {ref.uri} - Range: {ref.range}")

    anyio.run(main)
    ```

For more examples, see the `examples/` directory in the repository.
"""

from __future__ import annotations

from loguru import logger

from .client.abc import LSPClient
from .server.abc import LSPServer
from .utils.types import *  # noqa: F403

logger.disable(__name__)


def enable_logging() -> None:
    logger.enable(__name__)


def disable_logging() -> None:
    logger.disable(__name__)


# pdoc configuration
__docformat__ = "google"
__pdoc__ = {
    "logger": False,
}

__all__ = [
    "LSPClient",
    "LSPServer",
    "disable_logging",
    "enable_logging",
]
