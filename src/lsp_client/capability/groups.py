"""Some common capability groups."""

from __future__ import annotations

from typing import Protocol

import lsp_client.capability as lsp_cap


class FullFeaturedCapabilityGroup(
    lsp_cap.WithRequestReferences,
    lsp_cap.WithRequestDefinition,
    lsp_cap.WithRequestHover,
    lsp_cap.WithRequestCallHierarchy,
    lsp_cap.WithRequestCompletions,
    lsp_cap.WithRequestSignatureHelp,
    lsp_cap.WithRequestDocumentSymbols,
    lsp_cap.WithRequestWorkspaceSymbols,
    lsp_cap.WithReceiveLogMessage,
    lsp_cap.WithReceiveShowMessage,
    lsp_cap.WithReceiveLogTrace,
    lsp_cap.WithReceivePublishDiagnostics,
    Protocol,
    # TODO sync with implemented capabilities
):
    """
    All capabilities.

    Will always be synchronized with `lsp_client` supported capabilities.
    """
