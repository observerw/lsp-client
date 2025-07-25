from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any, Protocol, TypeGuard, override, runtime_checkable

from asyncio_addon import gather_all
from lsprotocol import types

from lsp_client.types import AnyPath, Position

from .protocol import LSPCapabilityClientProtocol, LSPCapabilityProtocol
from .utils import jsonrpc_uuid

logger = logging.getLogger(__name__)


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
    def client_capability(cls) -> types.ClientCapabilities:
        return types.ClientCapabilities(
            text_document=types.TextDocumentClientCapabilities(
                inline_completion=types.InlineCompletionClientCapabilities()
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: types.ServerCapabilities,
        info: types.ServerInfo | None,
    ):
        assert capability.inline_completion_provider
        logger.debug("Server supports textDocument/inlineCompletion checked")

    async def request_inline_completions(
        self,
        file_path: AnyPath,
        position: Position,
    ) -> Sequence[types.InlineCompletionItem] | None:
        match await self.request(
            types.InlineCompletionRequest(
                id=jsonrpc_uuid(),
                params=types.InlineCompletionParams(
                    context=types.InlineCompletionContext(
                        trigger_kind=types.InlineCompletionTriggerKind.Automatic,
                    ),
                    text_document=types.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                ),
            ),
            schema=types.InlineCompletionResponse,
            file_paths=[file_path],
        ):
            case types.InlineCompletionList(items=items) | items:
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
    def client_capability(cls) -> types.ClientCapabilities:
        return types.ClientCapabilities(
            workspace=types.WorkspaceClientCapabilities(
                execute_command=types.ExecuteCommandClientCapabilities()
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: types.ServerCapabilities,
        info: types.ServerInfo | None,
    ):
        assert capability.execute_command_provider
        logger.debug("Server supports workspace/executeCommand checked")

    async def request_execute_command(
        self, command: str, arguments: Sequence[Any] | None = None
    ) -> Any | None:
        return await self.request(
            types.ExecuteCommandRequest(
                id=jsonrpc_uuid(),
                params=types.ExecuteCommandParams(
                    command=command,
                    arguments=arguments,
                ),
            ),
            schema=types.ExecuteCommandResponse,
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
    def client_capability(cls) -> types.ClientCapabilities:
        return types.ClientCapabilities(
            text_document=types.TextDocumentClientCapabilities(
                references=types.ReferenceClientCapabilities()
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: types.ServerCapabilities,
        info: types.ServerInfo | None,
    ):
        assert capability.references_provider
        logger.debug("Server supports textDocument/references checked")

    async def request_references(
        self,
        file_path: AnyPath,
        position: Position,
        *,
        include_declaration: bool = False,
    ) -> Sequence[types.Location] | None:
        return await self.request(
            types.ReferencesRequest(
                id=jsonrpc_uuid(),
                params=types.ReferenceParams(
                    context=types.ReferenceContext(
                        include_declaration=include_declaration
                    ),
                    text_document=types.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                ),
            ),
            schema=types.ReferencesResponse,
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
    def client_capability(cls) -> types.ClientCapabilities:
        return types.ClientCapabilities(
            text_document=types.TextDocumentClientCapabilities(
                definition=types.DefinitionClientCapabilities(link_support=True)
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: types.ServerCapabilities,
        info: types.ServerInfo | None,
    ):
        assert capability.definition_provider
        logger.debug("Server supports textDocument/definition checked")

    @staticmethod
    def is_locations(result: list) -> TypeGuard[list[types.Location]]:
        return all(isinstance(item, types.Location) for item in result)

    @staticmethod
    def is_definition_links(result: list) -> TypeGuard[list[types.DefinitionLink]]:
        return all(isinstance(item, types.LocationLink) for item in result)

    async def request_definition(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[types.Location] | Sequence[types.DefinitionLink] | None:
        match await self.request(
            types.DefinitionRequest(
                id=jsonrpc_uuid(),
                params=types.DefinitionParams(
                    text_document=types.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                ),
            ),
            schema=types.DefinitionResponse,
            # file_paths=[file_path],
        ):
            case types.Location() as location:
                return [location]
            case list() as locations if self.is_locations(locations):
                return locations
            case list() as links if self.is_definition_links(links):
                return links


@runtime_checkable
class WithRequestDefinitionLocation(WithRequestDefinition, Protocol):
    """
    `textDocument/definition` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_definition
    """

    async def request_definition_location(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[types.Location] | None:
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
    ) -> Sequence[types.LocationLink] | None:
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
    def client_capability(cls) -> types.ClientCapabilities:
        return types.ClientCapabilities(
            text_document=types.TextDocumentClientCapabilities(
                hover=types.HoverClientCapabilities(
                    content_format=[
                        types.MarkupKind.Markdown,
                        types.MarkupKind.PlainText,
                    ]
                )
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: types.ServerCapabilities,
        info: types.ServerInfo | None,
    ):
        assert capability.hover_provider

        logger.debug("Server supports textDocument/hover checked")

    async def request_hover(
        self, file_path: AnyPath, position: Position
    ) -> types.Hover | None:
        return await self.request(
            types.HoverRequest(
                id=jsonrpc_uuid(),
                params=types.HoverParams(
                    text_document=types.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                ),
            ),
            schema=types.HoverResponse,
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
    def client_capability(cls) -> types.ClientCapabilities:
        return types.ClientCapabilities(
            text_document=types.TextDocumentClientCapabilities(
                call_hierarchy=types.CallHierarchyClientCapabilities()
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: types.ServerCapabilities,
        info: types.ServerInfo | None,
    ):
        assert capability.call_hierarchy_provider

        logger.debug("Server supports textDocument/callHierarchy checked")

    async def _prepare_call_hierarchy(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[types.CallHierarchyItem] | None:
        return await self.request(
            types.CallHierarchyPrepareRequest(
                id=jsonrpc_uuid(),
                params=types.CallHierarchyPrepareParams(
                    text_document=types.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                ),
            ),
            schema=types.CallHierarchyPrepareResponse,
            file_paths=[file_path],
        )

    async def request_call_hierarchy_incoming_call(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[types.CallHierarchyIncomingCall] | None:
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
                types.CallHierarchyIncomingCallsRequest(
                    id=jsonrpc_uuid(),
                    params=types.CallHierarchyIncomingCallsParams(item=prepare_result),
                ),
                schema=types.CallHierarchyIncomingCallsResponse,
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
    ) -> Sequence[types.CallHierarchyOutgoingCall] | None:
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
                types.CallHierarchyOutgoingCallsRequest(
                    id=jsonrpc_uuid(),
                    params=types.CallHierarchyOutgoingCallsParams(item=prepare_result),
                ),
                schema=types.CallHierarchyOutgoingCallsResponse,
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
    def client_capability(cls) -> types.ClientCapabilities:
        return types.ClientCapabilities(
            text_document=types.TextDocumentClientCapabilities(
                completion=types.CompletionClientCapabilities(
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
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: types.ServerCapabilities,
        info: types.ServerInfo | None,
    ):
        assert capability.completion_provider

        logger.debug("Server supports textDocument/completion checked")

    async def request_completions(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[types.CompletionItem] | None:
        match await self.request(
            types.CompletionRequest(
                id=jsonrpc_uuid(),
                params=types.CompletionParams(
                    text_document=types.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                ),
            ),
            schema=types.CompletionResponse,
            file_paths=[file_path],
        ):
            case types.CompletionList(items=items) | items:
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
    def client_capability(cls) -> types.ClientCapabilities:
        return types.ClientCapabilities(
            text_document=types.TextDocumentClientCapabilities(
                signature_help=types.SignatureHelpClientCapabilities()
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: types.ServerCapabilities,
        info: types.ServerInfo | None,
    ):
        assert capability.signature_help_provider

        logger.debug("Server supports textDocument/signatureHelp checked")

    async def request_signature_help(
        self, file_path: AnyPath, position: Position
    ) -> types.SignatureHelp | None:
        return await self.request(
            types.SignatureHelpRequest(
                id=jsonrpc_uuid(),
                params=types.SignatureHelpParams(
                    text_document=types.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                ),
            ),
            schema=types.SignatureHelpResponse,
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
    def client_capability(cls) -> types.ClientCapabilities:
        return types.ClientCapabilities(
            text_document=types.TextDocumentClientCapabilities(
                document_symbol=types.DocumentSymbolClientCapabilities(
                    symbol_kind=types.ClientSymbolKindOptions(
                        value_set=[*types.SymbolKind],
                    ),
                    tag_support=types.ClientSymbolTagOptions(
                        value_set=[
                            types.SymbolTag.Deprecated,
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
        capability: types.ServerCapabilities,
        info: types.ServerInfo | None,
    ):
        assert capability.document_symbol_provider

        logger.debug("Server supports textDocument/documentSymbol checked")

    async def _request_document_symbols(
        self, file_path: AnyPath
    ) -> Sequence[types.SymbolInformation] | Sequence[types.DocumentSymbol] | None:
        return await self.request(
            types.DocumentSymbolRequest(
                id=jsonrpc_uuid(),
                params=types.DocumentSymbolParams(
                    text_document=types.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                ),
            ),
            schema=types.DocumentSymbolResponse,
            file_paths=[file_path],
        )


@runtime_checkable
class WithRequestDocumentSymbolInformation(WithRequestDocumentSymbols, Protocol):
    """
    `textDocument/documentSymbol` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_documentSymbol
    """

    @staticmethod
    def is_symbol_information(result: list) -> TypeGuard[list[types.SymbolInformation]]:
        return all(isinstance(item, types.SymbolInformation) for item in result)

    async def request_document_symbol_information(
        self, file_path: AnyPath
    ) -> Sequence[types.SymbolInformation] | None:
        match await self._request_document_symbols(file_path):
            case list() as symbols if self.is_symbol_information(symbols):
                return symbols


@runtime_checkable
class WithRequestDocumentBaseSymbols(WithRequestDocumentSymbols, Protocol):
    """
    `textDocument/documentSymbol` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_documentSymbol
    """

    @staticmethod
    def is_document_symbols(result: list) -> TypeGuard[list[types.DocumentSymbol]]:
        return all(isinstance(item, types.DocumentSymbol) for item in result)

    async def request_document_symbols(
        self, file_path: AnyPath
    ) -> Sequence[types.DocumentSymbol] | None:
        match await self._request_document_symbols(file_path):
            case list() as symbols if self.is_document_symbols(symbols):
                return symbols


@runtime_checkable
class WithRequestWorkspaceSymbols(
    LSPCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def client_capability(cls) -> types.ClientCapabilities:
        return types.ClientCapabilities(
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
                )
            )
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        capability: types.ServerCapabilities,
        info: types.ServerInfo | None,
    ):
        assert capability.workspace_symbol_provider

        logger.debug("Server supports workspace/symbol checked")

    async def _request_workspace_symbols(
        self, query: str
    ) -> Sequence[types.SymbolInformation] | Sequence[types.WorkspaceSymbol] | None:
        return await self.request(
            types.WorkspaceSymbolRequest(
                id=jsonrpc_uuid(),
                params=types.WorkspaceSymbolParams(query=query),
            ),
            schema=types.WorkspaceSymbolResponse,
        )


@runtime_checkable
class WithRequestWorkspaceSymbolInformation(WithRequestWorkspaceSymbols, Protocol):
    """
    `workspace/symbol` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_symbol
    """

    @staticmethod
    def is_symbol_information(result: list) -> TypeGuard[list[types.SymbolInformation]]:
        return all(isinstance(item, types.SymbolInformation) for item in result)

    async def request_workspace_symbol_information(
        self, query: str
    ) -> Sequence[types.SymbolInformation] | None:
        match await self._request_workspace_symbols(query):
            case list() as symbols if self.is_symbol_information(symbols):
                return symbols


@runtime_checkable
class WithRequestWorkspaceBaseSymbols(WithRequestWorkspaceSymbols, Protocol):
    """
    `workspace/symbol` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_symbol
    """

    @staticmethod
    def is_workspace_symbols(result: list) -> TypeGuard[list[types.WorkspaceSymbol]]:
        return all(isinstance(item, types.WorkspaceSymbol) for item in result)

    async def request_workspace_symbols(
        self, query: str
    ) -> Sequence[types.WorkspaceSymbol] | None:
        match await self._request_workspace_symbols(query):
            case list() as symbols if self.is_workspace_symbols(symbols):
                return symbols
