"""
basedpyright: Language Server for Python - https://docs.basedpyright.com
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

import lsp_client.capability as cap
from lsp_client import lsp_type
from lsp_client.client import LSPClientBase


class BasedPyrightClient(
    cap.WithRequestReferences,
    cap.WithRequestDefinition,
    cap.WithRequestHover,
    cap.WithRequestCallHierarchy,
    cap.WithRequestCompletions,
    cap.WithRequestSignatureHelp,
    cap.WithRequestDocumentSymbols,
    cap.WithRequestWorkspaceSymbols,
    cap.WithReceiveLogMessage,
    cap.WithReceiveShowMessage,
    cap.WithReceiveLogTrace,
    cap.WithNotifyPublishDiagnostics,
    LSPClientBase,
):
    language_id: ClassVar[lsp_type.LanguageKind] = lsp_type.LanguageKind.Python
    server_cmd: ClassVar[Sequence[str]] = (
        "basedpyright-langserver",
        "--stdio",
    )
    client_capabilities: ClassVar[lsp_type.ClientCapabilities] = (
        lsp_type.ClientCapabilities(
            workspace=lsp_type.WorkspaceClientCapabilities(
                symbol=lsp_type.WorkspaceSymbolClientCapabilities(
                    symbol_kind=lsp_type.ClientSymbolKindOptions(
                        value_set=[*lsp_type.SymbolKind],
                    ),
                    tag_support=lsp_type.ClientSymbolTagOptions(
                        value_set=[
                            lsp_type.SymbolTag.Deprecated,
                        ]
                    ),
                    resolve_support=lsp_type.ClientSymbolResolveOptions(
                        properties=[
                            "location.range",
                        ]
                    ),
                ),
                diagnostics=lsp_type.DiagnosticWorkspaceClientCapabilities(
                    refresh_support=True,
                ),
            ),
            text_document=lsp_type.TextDocumentClientCapabilities(
                synchronization=lsp_type.TextDocumentSyncClientCapabilities(
                    will_save=True,
                    will_save_wait_until=True,
                    did_save=True,
                ),
                references=lsp_type.ReferenceClientCapabilities(),
                definition=lsp_type.DefinitionClientCapabilities(
                    link_support=True,
                ),
                hover=lsp_type.HoverClientCapabilities(
                    content_format=[
                        lsp_type.MarkupKind.Markdown,
                        lsp_type.MarkupKind.PlainText,
                    ],
                ),
                call_hierarchy=lsp_type.CallHierarchyClientCapabilities(),
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
                # type_hierarchy=lsp_type.TypeHierarchyClientCapabilities(),
                # type_definition=lsp_type.TypeDefinitionClientCapabilities(
                #     link_support=True,
                # ),
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
