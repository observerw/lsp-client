from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, TypeGuard, override, runtime_checkable

from asyncio_addon import gather_all
from loguru import logger

from lsp_client import lsp_type
from lsp_client.types import AnyPath, Position

from .protocol import LSPCapabilityClientProtocol, LSPCapabilityProtocol
from .utils import jsonrpc_uuid


@runtime_checkable
class WithRequestInlineCompletions(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/inlineCompletion` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.18/specification/#textDocument_inlineCompletion
    """

    @override
    @classmethod
    def client_capability(cls) -> lsp_type.ClientCapabilities:
        return lsp_type.ClientCapabilities(
            text_document=lsp_type.TextDocumentClientCapabilities(
                inline_completion=lsp_type.InlineCompletionClientCapabilities()
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        assert capability.inline_completion_provider
        logger.debug("Server supports textDocument/inlineCompletion checked")

    async def request_inline_completions(
        self,
        file_path: AnyPath,
        position: Position,
        *,
        info: lsp_type.SelectedCompletionInfo | None = None,
    ) -> Sequence[lsp_type.InlineCompletionItem] | None:
        match await self.request(
            lsp_type.InlineCompletionRequest(
                id=jsonrpc_uuid(),
                params=lsp_type.InlineCompletionParams(
                    context=lsp_type.InlineCompletionContext(
                        trigger_kind=lsp_type.InlineCompletionTriggerKind.Automatic,
                        selected_completion_info=info,
                    ),
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                ),
            ),
            schema=lsp_type.InlineCompletionResponse,
            file_paths=[file_path],
        ):
            case lsp_type.InlineCompletionList(items=items) | items:
                return items


@runtime_checkable
class WithRequestExecuteCommand(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    """
    `workspace/executeCommand` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_executeCommand
    """

    @override
    @classmethod
    def client_capability(cls) -> lsp_type.ClientCapabilities:
        return lsp_type.ClientCapabilities(
            workspace=lsp_type.WorkspaceClientCapabilities(
                execute_command=lsp_type.ExecuteCommandClientCapabilities()
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        assert capability.execute_command_provider
        logger.debug("Server supports workspace/executeCommand checked")

    async def request_execute_command(
        self, command: str, *arguments: Any
    ) -> Any | None:
        return await self.request(
            lsp_type.ExecuteCommandRequest(
                id=jsonrpc_uuid(),
                params=lsp_type.ExecuteCommandParams(
                    command=command,
                    arguments=arguments,
                ),
            ),
            schema=lsp_type.ExecuteCommandResponse,
        )


@runtime_checkable
class WithRequestReferences(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/references` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_references
    """

    @override
    @classmethod
    def client_capability(cls) -> lsp_type.ClientCapabilities:
        return lsp_type.ClientCapabilities(
            text_document=lsp_type.TextDocumentClientCapabilities(
                references=lsp_type.ReferenceClientCapabilities()
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        assert capability.references_provider
        logger.debug("Server supports textDocument/references checked")

    async def request_references(
        self,
        file_path: AnyPath,
        position: Position,
        *,
        include_declaration: bool = True,
    ) -> Sequence[lsp_type.Location] | None:
        return await self.request(
            lsp_type.ReferencesRequest(
                id=jsonrpc_uuid(),
                params=lsp_type.ReferenceParams(
                    context=lsp_type.ReferenceContext(
                        include_declaration=include_declaration
                    ),
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                ),
            ),
            schema=lsp_type.ReferencesResponse,
            file_paths=[file_path],
        )


@runtime_checkable
class WithRequestDefinition(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/definition` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_definition
    """

    @override
    @classmethod
    def client_capability(cls) -> lsp_type.ClientCapabilities:
        return lsp_type.ClientCapabilities(
            text_document=lsp_type.TextDocumentClientCapabilities(
                definition=lsp_type.DefinitionClientCapabilities(link_support=True)
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        assert capability.definition_provider
        logger.debug("Server supports textDocument/definition checked")

    @staticmethod
    def is_locations(result: list[Any]) -> TypeGuard[list[lsp_type.Location]]:
        return all(isinstance(item, lsp_type.Location) for item in result)

    @staticmethod
    def is_definition_links(
        result: list[Any],
    ) -> TypeGuard[list[lsp_type.DefinitionLink]]:
        return all(isinstance(item, lsp_type.LocationLink) for item in result)

    async def request_definition(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[lsp_type.Location] | Sequence[lsp_type.DefinitionLink] | None:
        match await self.request(
            lsp_type.DefinitionRequest(
                id=jsonrpc_uuid(),
                params=lsp_type.DefinitionParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                ),
            ),
            schema=lsp_type.DefinitionResponse,
            file_paths=[file_path],
        ):
            case lsp_type.Location() as location:
                return [location]
            case list() as locations if self.is_locations(locations):
                return locations
            case list() as links if self.is_definition_links(links):
                return links
            case _:
                return


@runtime_checkable
class WithRequestDefinitionLocation(WithRequestDefinition, Protocol):
    """
    `textDocument/definition` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_definition
    """

    async def request_definition_location(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[lsp_type.Location] | None:
        match await self.request_definition(file_path, position):
            case list() as result if self.is_locations(result):
                return result


@runtime_checkable
class WithRequestDefinitionLink(WithRequestDefinition, Protocol):
    """
    `textDocument/definition` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_definition

    Client should use this instead of {@WithRequestDefinitionLocation} whenever the server supports.
    """

    async def request_definition_link(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[lsp_type.LocationLink] | None:
        match await self.request_definition(file_path, position):
            case list() as result if self.is_definition_links(result):
                return result


@runtime_checkable
class WithRequestHover(LSPCapabilityProtocol, LSPCapabilityClientProtocol, Protocol):
    """
    `textDocument/hover` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_hover
    """

    @override
    @classmethod
    def client_capability(cls) -> lsp_type.ClientCapabilities:
        return lsp_type.ClientCapabilities(
            text_document=lsp_type.TextDocumentClientCapabilities(
                hover=lsp_type.HoverClientCapabilities(
                    content_format=[
                        lsp_type.MarkupKind.Markdown,
                        lsp_type.MarkupKind.PlainText,
                    ]
                )
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        assert capability.hover_provider

        logger.debug("Server supports textDocument/hover checked")

    async def request_hover(
        self, file_path: AnyPath, position: Position
    ) -> lsp_type.Hover | None:
        return await self.request(
            lsp_type.HoverRequest(
                id=jsonrpc_uuid(),
                params=lsp_type.HoverParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                ),
            ),
            schema=lsp_type.HoverResponse,
            file_paths=[file_path],
        )


@runtime_checkable
class WithRequestCallHierarchy(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    """
    `callHierarchy/prepare` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_prepareCallHierarchy
    `callHierarchy/incomingCalls` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#callHierarchy_incomingCalls
    `callHierarchy/outgoingCalls` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#callHierarchy_outgoingCalls
    """

    @override
    @classmethod
    def client_capability(cls) -> lsp_type.ClientCapabilities:
        return lsp_type.ClientCapabilities(
            text_document=lsp_type.TextDocumentClientCapabilities(
                call_hierarchy=lsp_type.CallHierarchyClientCapabilities()
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        assert capability.call_hierarchy_provider

        logger.debug("Server supports textDocument/callHierarchy checked")

    async def _prepare_call_hierarchy(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[lsp_type.CallHierarchyItem] | None:
        return await self.request(
            lsp_type.CallHierarchyPrepareRequest(
                id=jsonrpc_uuid(),
                params=lsp_type.CallHierarchyPrepareParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                ),
            ),
            schema=lsp_type.CallHierarchyPrepareResponse,
            file_paths=[file_path],
        )

    async def request_call_hierarchy_incoming_call(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[lsp_type.CallHierarchyIncomingCall] | None:
        """
        Note: For symbol with multiple definitions, this method will return a list of
        all incoming calls for each definition.
        """

        if not (
            prepare_results := await self._prepare_call_hierarchy(file_path, position)
        ):
            return

        result_groups = await gather_all(
            self.request(
                lsp_type.CallHierarchyIncomingCallsRequest(
                    id=jsonrpc_uuid(),
                    params=lsp_type.CallHierarchyIncomingCallsParams(
                        item=prepare_result
                    ),
                ),
                schema=lsp_type.CallHierarchyIncomingCallsResponse,
                file_paths=[file_path],
            )
            for prepare_result in prepare_results
        )

        return [
            result
            for result_group in result_groups
            if result_group
            for result in result_group
        ]

    async def request_call_hierarchy_outgoing_call(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[lsp_type.CallHierarchyOutgoingCall] | None:
        """
        Note: For symbol with multiple definitions, this method will return a list of
        all outgoing calls for each definition.
        """

        if not (
            prepare_results := await self._prepare_call_hierarchy(file_path, position)
        ):
            return

        result_groups = await gather_all(
            self.request(
                lsp_type.CallHierarchyOutgoingCallsRequest(
                    id=jsonrpc_uuid(),
                    params=lsp_type.CallHierarchyOutgoingCallsParams(
                        item=prepare_result
                    ),
                ),
                schema=lsp_type.CallHierarchyOutgoingCallsResponse,
                file_paths=[file_path],
            )
            for prepare_result in prepare_results
        )

        return [
            result
            for result_group in result_groups
            if result_group
            for result in result_group
        ]


@runtime_checkable
class WithRequestCompletions(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/completion` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_completion
    """

    @override
    @classmethod
    def client_capability(cls) -> lsp_type.ClientCapabilities:
        return lsp_type.ClientCapabilities(
            text_document=lsp_type.TextDocumentClientCapabilities(
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
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        assert capability.completion_provider
        logger.debug("Server supports textDocument/completion checked")

    async def request_completions(
        self,
        file_path: AnyPath,
        position: Position,
        *,
        trigger_kind: lsp_type.CompletionTriggerKind = lsp_type.CompletionTriggerKind.Invoked,
        trigger_character: str | None = None,
    ) -> Sequence[lsp_type.CompletionItem] | None:
        match await self.request(
            lsp_type.CompletionRequest(
                id=jsonrpc_uuid(),
                params=lsp_type.CompletionParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                    context=lsp_type.CompletionContext(
                        trigger_kind=trigger_kind,
                        trigger_character=trigger_character,
                    ),
                ),
            ),
            schema=lsp_type.CompletionResponse,
            file_paths=[file_path],
        ):
            case lsp_type.CompletionList(items=items) | items:
                return items


@runtime_checkable
class WithRequestSignatureHelp(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/signatureHelp` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_signatureHelp
    """

    @override
    @classmethod
    def client_capability(cls) -> lsp_type.ClientCapabilities:
        return lsp_type.ClientCapabilities(
            text_document=lsp_type.TextDocumentClientCapabilities(
                signature_help=lsp_type.SignatureHelpClientCapabilities()
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        assert capability.signature_help_provider

        logger.debug("Server supports textDocument/signatureHelp checked")

    async def request_signature_help(
        self,
        file_path: AnyPath,
        position: Position,
        *,
        trigger_kind: lsp_type.SignatureHelpTriggerKind = lsp_type.SignatureHelpTriggerKind.Invoked,
        is_retrigger: bool = False,
        trigger_character: str | None = None,
        active_signature_help: lsp_type.SignatureHelp | None = None,
    ) -> lsp_type.SignatureHelp | None:
        return await self.request(
            lsp_type.SignatureHelpRequest(
                id=jsonrpc_uuid(),
                params=lsp_type.SignatureHelpParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                    context=lsp_type.SignatureHelpContext(
                        trigger_kind=trigger_kind,
                        is_retrigger=is_retrigger,
                        trigger_character=trigger_character,
                        active_signature_help=active_signature_help,
                    ),
                ),
            ),
            schema=lsp_type.SignatureHelpResponse,
            file_paths=[file_path],
        )


@runtime_checkable
class WithRequestDocumentSymbols(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def client_capability(cls) -> lsp_type.ClientCapabilities:
        return lsp_type.ClientCapabilities(
            text_document=lsp_type.TextDocumentClientCapabilities(
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
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        assert capability.document_symbol_provider

        logger.debug("Server supports textDocument/documentSymbol checked")

    async def _request_document_symbols(
        self, file_path: AnyPath
    ) -> (
        Sequence[lsp_type.SymbolInformation] | Sequence[lsp_type.DocumentSymbol] | None
    ):
        return await self.request(
            lsp_type.DocumentSymbolRequest(
                id=jsonrpc_uuid(),
                params=lsp_type.DocumentSymbolParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                ),
            ),
            schema=lsp_type.DocumentSymbolResponse,
            file_paths=[file_path],
        )


@runtime_checkable
class WithRequestDocumentSymbolInformation(WithRequestDocumentSymbols, Protocol):
    """
    `textDocument/documentSymbol` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_documentSymbol
    """

    @staticmethod
    def is_symbol_information(
        result: list[Any],
    ) -> TypeGuard[list[lsp_type.SymbolInformation]]:
        return all(isinstance(item, lsp_type.SymbolInformation) for item in result)

    async def request_document_symbol_information(
        self, file_path: AnyPath
    ) -> Sequence[lsp_type.SymbolInformation] | None:
        match await self._request_document_symbols(file_path):
            case list() as symbols if self.is_symbol_information(symbols):
                return symbols


@runtime_checkable
class WithRequestDocumentBaseSymbols(WithRequestDocumentSymbols, Protocol):
    """
    `textDocument/documentSymbol` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_documentSymbol
    """

    @staticmethod
    def is_document_symbols(
        result: list[Any],
    ) -> TypeGuard[list[lsp_type.DocumentSymbol]]:
        return all(isinstance(item, lsp_type.DocumentSymbol) for item in result)

    async def request_document_symbols(
        self, file_path: AnyPath
    ) -> Sequence[lsp_type.DocumentSymbol] | None:
        match await self._request_document_symbols(file_path):
            case list() as symbols if self.is_document_symbols(symbols):
                return symbols
            case _:
                return


@runtime_checkable
class WithRequestWorkspaceSymbols(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def client_capability(cls) -> lsp_type.ClientCapabilities:
        return lsp_type.ClientCapabilities(
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
                )
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        assert capability.workspace_symbol_provider

        logger.debug("Server supports workspace/symbol checked")

    async def _request_workspace_symbols(
        self, query: str
    ) -> (
        Sequence[lsp_type.SymbolInformation] | Sequence[lsp_type.WorkspaceSymbol] | None
    ):
        return await self.request(
            lsp_type.WorkspaceSymbolRequest(
                id=jsonrpc_uuid(),
                params=lsp_type.WorkspaceSymbolParams(query=query),
            ),
            schema=lsp_type.WorkspaceSymbolResponse,
        )


@runtime_checkable
class WithRequestWorkspaceSymbolInformation(WithRequestWorkspaceSymbols, Protocol):
    """
    `workspace/symbol` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_symbol
    """

    @staticmethod
    def is_symbol_information(
        result: list[Any],
    ) -> TypeGuard[list[lsp_type.SymbolInformation]]:
        return all(isinstance(item, lsp_type.SymbolInformation) for item in result)

    async def request_workspace_symbol_information(
        self, query: str
    ) -> Sequence[lsp_type.SymbolInformation] | None:
        match await self._request_workspace_symbols(query):
            case list() as symbols if self.is_symbol_information(symbols):
                return symbols
            case _:
                return


@runtime_checkable
class WithRequestWorkspaceBaseSymbols(WithRequestWorkspaceSymbols, Protocol):
    """
    `workspace/symbol` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_symbol
    """

    @staticmethod
    def is_workspace_symbols(
        result: list[Any],
    ) -> TypeGuard[list[lsp_type.WorkspaceSymbol]]:
        return all(isinstance(item, lsp_type.WorkspaceSymbol) for item in result)

    async def request_workspace_symbols(
        self, query: str
    ) -> Sequence[lsp_type.WorkspaceSymbol] | None:
        match await self._request_workspace_symbols(query):
            case list() as symbols if self.is_workspace_symbols(symbols):
                return symbols
            case _:
                return
