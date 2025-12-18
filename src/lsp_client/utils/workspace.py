from __future__ import annotations

import os
from collections.abc import Mapping
from functools import cached_property
from pathlib import Path
from typing import Final

import attrs

from .types import AnyPath, lsp_type
from .uri import from_local_uri


@attrs.define
class WorkspaceFolder(lsp_type.WorkspaceFolder):
    @cached_property
    def path(self) -> Path:
        return from_local_uri(self.uri)


# type Workspace = Mapping[str, WorkspaceFolder]


class Workspace(dict[str, WorkspaceFolder]):
    def to_folders(self) -> list[WorkspaceFolder]:
        return list(self.values())


DEFAULT_WORKSPACE_PATH = Path.cwd()
DEFAULT_WORKSPACE_DIR: Final = "__root__"
DEFAULT_WORKSPACE: Final[Workspace] = Workspace(
    {
        DEFAULT_WORKSPACE_DIR: WorkspaceFolder(
            uri=Path.cwd().as_uri(),
            name=DEFAULT_WORKSPACE_DIR,
        )
    }
)

type RawWorkspace = AnyPath | Mapping[str, AnyPath]


def workspace_converter(raw: RawWorkspace) -> Workspace:
    match raw:
        case str() | os.PathLike() as root_folder_path:
            return Workspace(
                {
                    DEFAULT_WORKSPACE_DIR: WorkspaceFolder(
                        uri=Path(root_folder_path).as_uri(),
                        name="root",
                    )
                }
            )
        case _ as mapping:
            return Workspace(
                {
                    name: WorkspaceFolder(uri=Path(path).as_uri(), name=name)
                    for name, path in mapping.items()
                }
            )
