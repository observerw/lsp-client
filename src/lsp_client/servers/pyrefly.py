"""
pyrefly: Type checker and language server for Python - https://pyrefly.org/
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import ClassVar, override

from semver import Version

from lsp_client import LSPClientBase, lsp_cap, lsp_type

logger = logging.getLogger(__name__)


class PyReflyClient(
    lsp_cap.WithRequestReferences,
    lsp_cap.WithRequestDocumentSymbols,
    lsp_cap.WithRequestHover,
    lsp_cap.WithRequestSignatureHelp,
    lsp_cap.WithRequestCompletions,
    lsp_cap.WithNotifyPublishDiagnostics,
    lsp_cap.WithReceiveLogMessage,
    lsp_cap.WithReceiveShowMessage,
    lsp_cap.WithReceiveLogTrace,
    lsp_cap.WithRespondWorkspaceFolders,
    LSPClientBase,
):
    """
    Keep track of <https://github.com/facebook/pyrefly/issues/344> for LSP features support.
    """

    language_id: ClassVar[lsp_type.LanguageKind] = lsp_type.LanguageKind.Python
    server_cmd: ClassVar[Sequence[str]] = (
        "pyrefly",
        "lsp",
        "-v",
    )

    client_capabilities: ClassVar[lsp_type.ClientCapabilities] = (
        lsp_type.ClientCapabilities(
            workspace=lsp_type.WorkspaceClientCapabilities(
                diagnostics=lsp_type.DiagnosticWorkspaceClientCapabilities(
                    refresh_support=True,
                ),
                workspace_folders=True,
            ),
            text_document=lsp_type.TextDocumentClientCapabilities(
                synchronization=lsp_type.TextDocumentSyncClientCapabilities(
                    will_save=True,
                    will_save_wait_until=True,
                    did_save=True,
                ),
                references=lsp_type.ReferenceClientCapabilities(),
                hover=lsp_type.HoverClientCapabilities(
                    content_format=[
                        lsp_type.MarkupKind.Markdown,
                        lsp_type.MarkupKind.PlainText,
                    ],
                ),
                completion=lsp_type.CompletionClientCapabilities(
                    completion_item=lsp_type.ClientCompletionItemOptions(
                        snippet_support=True,
                        commit_characters_support=True,
                        documentation_format=[
                            lsp_type.MarkupKind.Markdown,
                            lsp_type.MarkupKind.PlainText,
                        ],
                        deprecated_support=True,
                        preselect_support=True,
                        tag_support=lsp_type.CompletionItemTagOptions(
                            value_set=[lsp_type.CompletionItemTag.Deprecated]
                        ),
                    ),
                ),
                signature_help=lsp_type.SignatureHelpClientCapabilities(
                    signature_information=lsp_type.ClientSignatureInformationOptions(
                        documentation_format=[
                            lsp_type.MarkupKind.Markdown,
                            lsp_type.MarkupKind.PlainText,
                        ],
                        parameter_information=lsp_type.ClientSignatureParameterInformationOptions(
                            label_offset_support=True,
                        ),
                    ),
                ),
                document_symbol=lsp_type.DocumentSymbolClientCapabilities(
                    symbol_kind=lsp_type.ClientSymbolKindOptions(
                        value_set=[*lsp_type.SymbolKind],
                    ),
                    tag_support=lsp_type.ClientSymbolTagOptions(
                        value_set=[
                            lsp_type.SymbolTag.Deprecated,
                        ]
                    ),
                    hierarchical_document_symbol_support=True,
                ),
            ),
            window=lsp_type.WindowClientCapabilities(
                show_message=lsp_type.ShowMessageRequestClientCapabilities(
                    message_action_item=lsp_type.ClientShowMessageActionItemOptions(
                        additional_properties_support=True,
                    ),
                ),
                show_document=lsp_type.ShowDocumentClientCapabilities(
                    support=True,
                ),
            ),
            general=lsp_type.GeneralClientCapabilities(
                regular_expressions=lsp_type.RegularExpressionsClientCapabilities(
                    engine="ECMAScript",
                    version="ES2020",
                ),
                position_encodings=["utf-16"],
            ),
        )
    )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        if info and (version := info.version):
            assert Version.parse(version).match(">=0.24")

            logger.debug(
                "Server version %s supports PyReflyClient capabilities",
                version,
            )
