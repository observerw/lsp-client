from typing import ClassVar

from lsprotocol import types

import lsp_client.capability as cap
from lsp_client.client import LSPClientBase


class BasedPyrightClient(
    cap.WithRequestReferences,
    cap.WithRequestDefinition,
    cap.WithRequestHover,
    cap.WithReceiveLogMessage,
    cap.WithReceiveShowMessage,
    cap.WithReceiveLogTrace,
    LSPClientBase,
):
    language_id: ClassVar = types.LanguageKind.Python
    server_cmd: ClassVar = (
        "basedpyright-langserver",
        "--stdio",
    )
    client_capabilities: ClassVar[types.ClientCapabilities] = types.ClientCapabilities(
        workspace=types.WorkspaceClientCapabilities(
            symbol=types.WorkspaceSymbolClientCapabilities(
                symbol_kind=types.ClientSymbolKindOptions(
                    value_set=[*types.SymbolKind],
                ),
                tag_support=types.ClientSymbolTagOptions(
                    value_set=[
                        types.SymbolTag.Deprecated,
                    ]
                ),
                resolve_support=types.ClientSymbolResolveOptions(
                    properties=[
                        "location.range",
                    ]
                ),
            ),
        ),
        text_document=types.TextDocumentClientCapabilities(
            synchronization=types.TextDocumentSyncClientCapabilities(
                dynamic_registration=True,
                will_save=True,
                will_save_wait_until=True,
                did_save=True,
            ),
            completion=types.CompletionClientCapabilities(
                dynamic_registration=True,
                completion_item=types.ClientCompletionItemOptions(
                    snippet_support=True,
                    commit_characters_support=True,
                    documentation_format=[
                        types.MarkupKind.Markdown,
                        types.MarkupKind.PlainText,
                    ],
                    deprecated_support=True,
                    preselect_support=True,
                    tag_support=types.CompletionItemTagOptions(
                        value_set=[types.CompletionItemTag.Deprecated]
                    ),
                ),
            ),
            hover=types.HoverClientCapabilities(
                content_format=[
                    types.MarkupKind.Markdown,
                    types.MarkupKind.PlainText,
                ],
            ),
            definition=types.DefinitionClientCapabilities(
                link_support=True,
            ),
            type_definition=types.TypeDefinitionClientCapabilities(
                link_support=True,
            ),
            references=types.ReferenceClientCapabilities(
                dynamic_registration=True,
            ),
            call_hierarchy=types.CallHierarchyClientCapabilities(
                dynamic_registration=True,
            ),
            type_hierarchy=types.TypeHierarchyClientCapabilities(
                dynamic_registration=True,
            ),
        ),
        window=types.WindowClientCapabilities(
            show_message=types.ShowMessageRequestClientCapabilities(
                message_action_item=types.ClientShowMessageActionItemOptions(
                    additional_properties_support=True,
                ),
            ),
            show_document=types.ShowDocumentClientCapabilities(
                support=True,
            ),
        ),
        general=types.GeneralClientCapabilities(
            regular_expressions=types.RegularExpressionsClientCapabilities(
                engine="ECMAScript",
                version="ES2020",
            ),
            position_encodings=["utf-16"],
        ),
    )
