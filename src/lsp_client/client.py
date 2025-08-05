from __future__ import annotations

import os
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from lsp_client import jsonrpc
from lsp_client.server import LSPServerPool
from lsp_client.server.base import ServerArgs, ServerRuntimeArgs
from lsp_client.types import AnyPath
from lsp_client.utils.path import AbsPath

from .capability.client import (
    ROOT_FOLDER_NAME,
    ClientArgs,
    ClientRuntimeArgs,
    LSPCapabilityClientBase,
    WorkspaceFolder,
)


@dataclass(frozen=True)
class LSPClientBase[Client: LSPCapabilityClientBase[Any]](
    ServerArgs,
    ClientArgs,
    ABC,
):
    buffer_size: int = 0

    @asynccontextmanager
    @abstractmethod
    def _start_client(
        self,
        args: ClientArgs,
        runtime_args: ClientRuntimeArgs,
    ) -> AsyncGenerator[Client]:
        """Start the LSP capability client."""

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
                        uri=AbsPath(root_folder_path).as_uri(),
                        name=ROOT_FOLDER_NAME,
                    )
                ]
            case _ as mapping:
                workspace_folders = [
                    WorkspaceFolder(uri=AbsPath(path).as_uri(), name=name)
                    for name, path in mapping.items()
                ]

        # client-side request channel
        ctx, srx = jsonrpc.request_channel.create(self.buffer_size)
        # server-side request channel
        stx, crx = jsonrpc.request_channel.create(self.buffer_size)

        async with (
            LSPServerPool.start(
                args=self,
                runtime_args=ServerRuntimeArgs(
                    sender=stx,
                    receiver=srx,
                ),
            ) as server,
            self._start_client(
                args=self,
                runtime_args=ClientRuntimeArgs(
                    sender=ctx,
                    receiver=crx,
                    server_count=server.process_count,
                    workspace_folders=workspace_folders,
                ),
            ) as client,
        ):
            yield client
