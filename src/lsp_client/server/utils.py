from __future__ import annotations

from lsp_client.types import Workspace


def container_volume_args(workspace: Workspace) -> list[str]:
    return [f"-v {path}:{path}" for path in workspace.values()]
