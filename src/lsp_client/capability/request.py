from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, TypeGuard, override, runtime_checkable

from lsprotocol import types

from lsp_client.types import AnyPath, Position

from .client import LSPCapabilityClient
from .utils import jsonrpc_uuid


@runtime_checkable
class WithRequestInlineCompletions(LSPCapabilityClient, Protocol):
    """
    `textDocument/inlineCompletion` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.18/specification/#textDocument_inlineCompletion
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.inline_completion

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert capability.inline_completion_provider

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
        ):
            case types.InlineCompletionList(items=items) | items:
                return items


@runtime_checkable
class WithRequestExecuteCommand(LSPCapabilityClient, Protocol):
    """
    `workspace/executeCommand` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_executeCommand
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (workspace := cls.client_capabilities.workspace)
        assert workspace.execute_command

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert capability.execute_command_provider

    async def request_execute_command(
        self, command: str, arguments: Sequence[Any] | None = None
    ) -> types.ExecuteCommandResult:
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
class WithRequestReferences(LSPCapabilityClient, Protocol):
    """
    `textDocument/references` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_references
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.references

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert capability.references_provider

    async def request_references(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[types.Location] | None:
        return await self.request(
            types.ReferencesRequest(
                id=jsonrpc_uuid(),
                params=types.ReferenceParams(
                    context=types.ReferenceContext(include_declaration=False),
                    text_document=types.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                ),
            ),
            schema=types.ReferencesResponse,
        )


@runtime_checkable
class WithRequestDefinitionBase(LSPCapabilityClient, Protocol):
    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.definition

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert capability.definition_provider

    async def _request_definition(
        self, file_path: AnyPath, position: Position
    ) -> types.DefinitionResult:
        return await self.request(
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
        )


@runtime_checkable
class WithRequestDefinitionLocation(WithRequestDefinitionBase, Protocol):
    """
    `textDocument/definition` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_definition
    """

    @staticmethod
    def is_locations(result: list) -> TypeGuard[list[types.Location]]:
        return all(isinstance(item, types.Location) for item in result)

    async def request_definition_location(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[types.Location] | None:
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
        ):
            case types.Location() as location:
                return [location]
            case list() as locations if self.is_locations(locations):
                return locations


@runtime_checkable
class WithRequestDefinition(WithRequestDefinitionBase, Protocol):
    """
    `textDocument/definition` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_definition

    Client should use this instead of {@WithRequestDefinitionLocation} whenever the server supports.
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.definition
        assert text_document.definition.link_support

    @staticmethod
    def is_definition_links(result: list) -> TypeGuard[list[types.DefinitionLink]]:
        return all(isinstance(item, types.DefinitionLink) for item in result)

    async def request_definition(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[types.DefinitionLink] | None:
        match await self._request_definition(file_path, position):
            case list() as result if self.is_definition_links(result):
                return result


@runtime_checkable
class WithRequestHover(LSPCapabilityClient, Protocol):
    """
    `textDocument/hover` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_hover
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.hover

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert capability.hover_provider

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
        )


@runtime_checkable
class WithRequestCallHierarchy(LSPCapabilityClient, Protocol):
    """
    `callHierarchy/prepare` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#callHierarchy_prepare
    `callHierarchy/incomingCalls` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#callHierarchy_incomingCalls
    `callHierarchy/outgoingCalls` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#callHierarchy_outgoingCalls
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.call_hierarchy

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert capability.call_hierarchy_provider

    async def _prepare_call_hierarchy(
        self, file_path: AnyPath, position: Position
    ) -> types.CallHierarchyPrepareResult:
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
        )

    async def request_call_hierarchy_incoming_call(
        self, file_path: AnyPath, position: Position
    ) -> types.CallHierarchyIncomingCallsResult:
        raise NotImplementedError

    async def request_call_hierarchy_outgoing_call(
        self, file_path: AnyPath, position: Position
    ) -> types.CallHierarchyOutgoingCallsResult:
        raise NotImplementedError


@runtime_checkable
class WithRequestCompletions(LSPCapabilityClient, Protocol):
    """
    `textDocument/completion` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_completion
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.completion

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert capability.completion_provider

    async def request_completions(
        self,
        file_path: AnyPath,
        position: Position,
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
        ):
            case types.CompletionList(items=items) | items:
                return items


@runtime_checkable
class WithRequestSignatureHelp(LSPCapabilityClient, Protocol):
    """
    `textDocument/signatureHelp` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_signatureHelp
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.signature_help

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert capability.signature_help_provider

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
        )


@runtime_checkable
class WithRequestDocumentSymbolsBase(LSPCapabilityClient, Protocol):
    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.document_symbol

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert capability.document_symbol_provider

    async def _request_document_symbols(
        self, file_path: AnyPath
    ) -> types.DocumentSymbolResult:
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
        )


@runtime_checkable
class WithRequestDocumentSymbolInformation(WithRequestDocumentSymbolsBase, Protocol):
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
class WithRequestDocumentSymbols(WithRequestDocumentSymbolsBase, Protocol):
    """
    `textDocument/documentSymbol` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_documentSymbol
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.document_symbol
        assert text_document.document_symbol.hierarchical_document_symbol_support

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
class WithRequestWorkspaceSymbolsBase(LSPCapabilityClient, Protocol):
    @override
    @classmethod
    def check_client_capability(cls):
        assert (workspace := cls.client_capabilities.workspace)
        assert workspace.symbol

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert capability.workspace_symbol_provider

    async def _request_workspace_symbols(
        self, query: str
    ) -> types.WorkspaceSymbolResult:
        return await self.request(
            types.WorkspaceSymbolRequest(
                id=jsonrpc_uuid(), params=types.WorkspaceSymbolParams(query=query)
            ),
            schema=types.WorkspaceSymbolResponse,
        )


@runtime_checkable
class WithRequestWorkspaceSymbolInformation(WithRequestWorkspaceSymbolsBase, Protocol):
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
class WithRequestWorkspaceSymbols(WithRequestWorkspaceSymbolsBase, Protocol):
    """
    `workspace/symbol` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_symbol
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (workspace := cls.client_capabilities.workspace)
        assert workspace.symbol
        assert workspace.symbol.resolve_support

    @staticmethod
    def is_workspace_symbols(result: list) -> TypeGuard[list[types.WorkspaceSymbol]]:
        return all(isinstance(item, types.WorkspaceSymbol) for item in result)

    async def request_workspace_symbols(
        self, query: str
    ) -> Sequence[types.WorkspaceSymbol] | None:
        match await self._request_workspace_symbols(query):
            case list() as symbols if self.is_workspace_symbols(symbols):
                return symbols
