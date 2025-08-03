from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Mapping, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from functools import cached_property

from lsp_client.server import LSPServerInfo, LSPServerPool, ServerRequestQueue
from lsp_client.types import AnyPath
from lsp_client.utils.path import AbsPath

from .capability.client import (
    ROOT_FOLDER_NAME,
    LSPCapabilityClientBase,
    WorkspaceFolder,
)


@dataclass(frozen=True)
class LSPClientBase[Client: LSPCapabilityClientBase](ABC):
    sync_file: bool = True
    """Whether to synchronize file (open, close, changed, etc.) when performing file-related operations."""

    server_count: int | None = 1
    """The number of LSP server processes to start. If None, defaults to the number of CPU cores."""

    server_info: LSPServerInfo = field(default_factory=LSPServerInfo)
    """Runtime information for the LSP server."""

    pending_timeout: float | None = 10
    """Timeout for pending requests in seconds."""

    @cached_property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.__name__)

    @abstractmethod
    @asynccontextmanager
    def _start_client(
        self,
        server: LSPServerPool,
        workspace: Sequence[WorkspaceFolder],
    ) -> AsyncGenerator[Client]:
        """Start the LSP client and yield the client instance."""

    @asynccontextmanager
    async def start(
        self, workspace: AnyPath | Mapping[str, AnyPath]
    ) -> AsyncGenerator[Client]:
        """
        Start the LSP client.

        Args:
            workspace (AnyPath | Mapping[str, AnyPath]):
                The workspace to use. Can be a single path or a mapping of folder names to paths for multi-root workspaces.

        Yields:
            Client: The LSP client instance.

        Examples:
            Start with a single workspace path:

            ```python
            async with client.start("/path/to/workspace") as lsp_client:
                ...
            ```

            Start with multiple workspace folders:

            ```python
            async with client.start({
                "workspace_1": "/path/to/workspace1",
                "workspace_2": "/path/to/workspace2",
            }) as lsp_client:
                ...
            ```

        For multi-root workspaces, the `workspace` argument can be a mapping where keys are folder names and values are their paths.
        You can reference these folders by their names in file paths:

        ```python
        async with client.start({
            "src": "/path/to/src",
        }) as lsp_client:
            # client will perform operations in "/path/to/src/main.py"
            refs = await client.request_references("src/main.py", Position(10, 20))
        ```
        """

        match workspace:
            case str() | os.PathLike() as root_folder_path:
                workspace_folders = [
                    WorkspaceFolder(
                        path=AbsPath(root_folder_path),
                        name=ROOT_FOLDER_NAME,
                    )
                ]
            case _ as mapping:
                workspace_folders = [
                    WorkspaceFolder(path=AbsPath(path), name=name)
                    for name, path in mapping.items()
                ]

        server_req_queue = ServerRequestQueue()
        async with (
            LSPServerPool.load(
                server_cmd=self.server_cmd,
                server_req_queue=server_req_queue,
                process_count=self.server_count,
                info=self.server_info,
                pending_timeout=self.pending_timeout,
            ) as server,
            self._start_client(
                server,
                workspace_folders,
            ) as client,
        ):
            yield client

    @property
    @abstractmethod
    def server_cmd(self) -> Sequence[str]:
        """The command to start the LSP server."""
