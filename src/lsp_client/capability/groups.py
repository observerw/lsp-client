"""Some common capability groups."""

from __future__ import annotations

from typing import Protocol

from . import request as req
from . import response as resp


class FullFeaturedCapabilityGroup(
    req.WithRequestReferences,
    req.WithRequestDefinition,
    req.WithRequestHover,
    req.WithRequestCallHierarchy,
    req.WithRequestCompletions,
    req.WithRequestSignatureHelp,
    req.WithRequestDocumentSymbols,
    req.WithRequestWorkspaceSymbols,
    resp.WithReceiveLogMessage,
    resp.WithReceiveShowMessage,
    resp.WithReceiveLogTrace,
    resp.WithReceivePublishDiagnostics,
    Protocol,
    # TODO sync with implemented capabilities
):
    """
    All capabilities.

    Will always be synchronized with `lsp_client` supported capabilities.
    """
