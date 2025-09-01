"""Re-export some lsp types for convenience."""

from __future__ import annotations

import os
from collections.abc import Mapping
from functools import cached_property
from pathlib import Path
from typing import Protocol

import attrs
from attrs import AttrsInstance
from lsprotocol import types as lsp_type

from lsp_client.utils.path import from_local_uri

Position = lsp_type.Position
Range = lsp_type.Range

AnyPath = str | os.PathLike[str]

type Request = AttrsInstance
type Notification = AttrsInstance


class Response[T](Protocol):
    """
    Duck-type schema for extracting the result type from `lsprotocol` Response schema.

    e.g.

    ```python
    def result[T](self, resp: Response[T]) -> T:
        return resp.result
    ```
    """

    result: T


@attrs.define
class WorkspaceFolder(lsp_type.WorkspaceFolder):
    @cached_property
    def path(self) -> Path:
        return from_local_uri(self.uri)


type Workspace = Mapping[str, WorkspaceFolder]
