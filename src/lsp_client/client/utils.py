from __future__ import annotations

import os
from collections.abc import Mapping

from lsp_client.types import AnyPath, Workspace, WorkspaceFolder
from lsp_client.utils.path import AbsPath

type RawWorkspace = AnyPath | Mapping[str, AnyPath]
ROOT_FOLDER_NAME = "__root__"


def format_workspace(raw: RawWorkspace) -> Workspace:
    match raw:
        case str() | os.PathLike() as root_folder_path:
            return {
                ROOT_FOLDER_NAME: WorkspaceFolder(
                    uri=AbsPath(root_folder_path).as_uri(),
                    name=ROOT_FOLDER_NAME,
                )
            }
        case _ as mapping:
            return {
                name: WorkspaceFolder(uri=AbsPath(path).as_uri(), name=name)
                for name, path in mapping.items()
            }
