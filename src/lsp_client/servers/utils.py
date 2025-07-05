import os

from lsprotocol import types

from lsp_client.utils.path import AbsPath


def initialize_params(
    root_path: AbsPath,
    capabilities: types.ClientCapabilities,
    *,
    initialization_options: dict | None = None,
) -> types.InitializeParams:
    """Return partial initialization parameters for the language server."""

    root_uri = root_path.as_uri()
    root_path_posix = root_path.as_posix()

    return types.InitializeParams(
        capabilities=capabilities,
        # current pid
        process_id=os.getpid(),
        client_info=types.ClientInfo(
            name="LSP Client",
            version="1.81.0-insider",
        ),
        locale="en-us",
        root_path=root_path_posix,
        root_uri=root_uri,
        initialization_options=initialization_options,
        trace=types.TraceValue.Verbose,
        workspace_folders=[
            types.WorkspaceFolder(
                uri=root_uri,
                name=root_path.name,
            )
        ],
    )
