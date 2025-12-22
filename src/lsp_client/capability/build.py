from __future__ import annotations

from typing import Any

from lsp_client.protocol import (
    ExperimentalCapabilityProtocol,
    GeneralCapabilityProtocol,
    NotebookCapabilityProtocol,
    ServerRequestHookProtocol,
    ServerRequestHookRegistry,
    TextDocumentCapabilityProtocol,
    WindowCapabilityProtocol,
    WorkspaceCapabilityProtocol,
)
from lsp_client.utils.types import lsp_type


def build_client_capabilities(cls: type) -> lsp_type.ClientCapabilities:
    workspace = lsp_type.WorkspaceClientCapabilities()
    text_document = lsp_type.TextDocumentClientCapabilities()
    notebook_document = lsp_type.NotebookDocumentClientCapabilities(
        synchronization=lsp_type.NotebookDocumentSyncClientCapabilities(),
    )
    window = lsp_type.WindowClientCapabilities()
    general = lsp_type.GeneralClientCapabilities()
    experimental: dict[str, Any] = {}

    if issubclass(cls, WorkspaceCapabilityProtocol):
        cls.register_workspace_capability(workspace)
    if issubclass(cls, TextDocumentCapabilityProtocol):
        cls.register_text_document_capability(text_document)
    if issubclass(cls, NotebookCapabilityProtocol):
        cls.register_notebook_document_capability(notebook_document)
    if issubclass(cls, WindowCapabilityProtocol):
        cls.register_window_capability(window)
    if issubclass(cls, GeneralCapabilityProtocol):
        cls.register_general_capability(general)
    if issubclass(cls, ExperimentalCapabilityProtocol):
        cls.register_experimental_capability(experimental)

    return lsp_type.ClientCapabilities(
        workspace=workspace,
        text_document=text_document,
        notebook_document=notebook_document,
        window=window,
        general=general,
        experimental=experimental or None,
    )


def build_server_request_hooks(instance: Any) -> ServerRequestHookRegistry:
    registry = ServerRequestHookRegistry()

    if isinstance(instance, ServerRequestHookProtocol):
        instance.register_server_request_hooks(registry)

    return registry
