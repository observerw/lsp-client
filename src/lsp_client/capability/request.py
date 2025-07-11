from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any, Protocol, TypeGuard, override, runtime_checkable

from asyncio_addon import gather_all
from lsprotocol import types

from lsp_client.types import AnyPath, Position

from .client import LSPCapabilityClient
from .utils import jsonrpc_uuid

logger = logging.getLogger(__name__)


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

        logger.debug("Client supports for textDocument/inlineCompletion checked")

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
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

        logger.debug("Client supports workspace/executeCommand checked")

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
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
class WithRequestReferences(LSPCapabilityClient, Protocol):
    """
    `textDocument/references` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_references
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.references

        logger.debug("Client supports textDocument/references checked")

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert capability.references_provider

        logger.debug("Server supports textDocument/references checked")

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
class WithRequestDefinition(LSPCapabilityClient, Protocol):
    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.definition

        logger.debug("Client supports textDocument/definition checked")

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
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

    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.definition
        assert text_document.definition.link_support

        logger.debug("Client supports textDocument/definition with linkSupport checked")

    async def request_definition_link(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[types.LocationLink] | None:
        match await self.request_definition(file_path, position):
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

        logger.debug("Client supports textDocument/hover checked")

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
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
        )


@runtime_checkable
class WithRequestCallHierarchy(LSPCapabilityClient, Protocol):
    """
    `callHierarchy/prepare` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_prepareCallHierarchy
    `callHierarchy/incomingCalls` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#callHierarchy_incomingCalls
    `callHierarchy/outgoingCalls` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#callHierarchy_outgoingCalls
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.call_hierarchy

        logger.debug("Client supports textDocument/callHierarchy checked")

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
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
class WithRequestCompletions(LSPCapabilityClient, Protocol):
    """
    `textDocument/completion` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_completion
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.completion

        logger.debug("Client supports textDocument/completion checked")

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
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

        logger.debug("Client supports textDocument/signatureHelp checked")

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
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
        )


@runtime_checkable
class WithRequestDocumentSymbols(LSPCapabilityClient, Protocol):
    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.document_symbol

        logger.debug("Client supports textDocument/documentSymbol checked")

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
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

    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.document_symbol
        assert text_document.document_symbol.hierarchical_document_symbol_support

        logger.debug(
            "Client supports textDocument/documentSymbol with hierarchical support checked"
        )

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
class WithRequestWorkspaceSymbols(LSPCapabilityClient, Protocol):
    @override
    @classmethod
    def check_client_capability(cls):
        assert (workspace := cls.client_capabilities.workspace)
        assert workspace.symbol

        logger.debug("Client supports workspace/symbol checked")

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert capability.workspace_symbol_provider

        logger.debug("Server supports workspace/symbol checked")

    async def _request_workspace_symbols(
        self, query: str
    ) -> Sequence[types.SymbolInformation] | Sequence[types.WorkspaceSymbol] | None:
        return await self.request(
            types.WorkspaceSymbolRequest(
                id=jsonrpc_uuid(), params=types.WorkspaceSymbolParams(query=query)
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

    @override
    @classmethod
    def check_client_capability(cls):
        assert (workspace := cls.client_capabilities.workspace)
        assert workspace.symbol
        assert workspace.symbol.resolve_support

        logger.debug("Client supports workspace/symbol with resolveSupport checked")

    @staticmethod
    def is_workspace_symbols(result: list) -> TypeGuard[list[types.WorkspaceSymbol]]:
        return all(isinstance(item, types.WorkspaceSymbol) for item in result)

    async def request_workspace_symbols(
        self, query: str
    ) -> Sequence[types.WorkspaceSymbol] | None:
        match await self._request_workspace_symbols(query):
            case list() as symbols if self.is_workspace_symbols(symbols):
                return symbols
