from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

import asyncer
from lsprotocol.types import TextDocumentClientCapabilities

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import CapabilityClientProtocol, TextDocumentCapabilityProtocol
from lsp_client.utils.types import AnyPath, Position, lsp_type


@runtime_checkable
class WithRequestCallHierarchy(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `callHierarchy/prepare` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_prepareCallHierarchy
    `callHierarchy/incomingCalls` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#callHierarchy_incomingCalls
    `callHierarchy/outgoingCalls` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#callHierarchy_outgoingCalls
    """

    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (
            lsp_type.TEXT_DOCUMENT_PREPARE_CALL_HIERARCHY,
            lsp_type.CALL_HIERARCHY_INCOMING_CALLS,
            lsp_type.CALL_HIERARCHY_OUTGOING_CALLS,
        )

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: TextDocumentClientCapabilities
    ) -> None:
        super().register_text_document_capability(cap)
        cap.call_hierarchy = lsp_type.CallHierarchyClientCapabilities()

    @override
    @classmethod
    def check_server_capability(
        cls,
        cap: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ):
        super().check_server_capability(cap, info)
        assert cap.call_hierarchy_provider

    async def prepare_call_hierarchy(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[lsp_type.CallHierarchyItem] | None:
        return await self.file_request(
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
    ) -> list[lsp_type.CallHierarchyIncomingCall] | None:
        """
        Note: For symbol with multiple definitions, this method will return a list of
        all incoming calls for each definition.
        """

        prepared = await self.prepare_call_hierarchy(file_path, position)

        if not prepared:
            return None

        calls: list[lsp_type.CallHierarchyIncomingCall] = []

        async def request(item: lsp_type.CallHierarchyItem) -> None:
            if resp := await self.file_request(
                req=lsp_type.CallHierarchyIncomingCallsRequest(
                    id=jsonrpc_uuid(),
                    params=lsp_type.CallHierarchyIncomingCallsParams(item=item),
                ),
                schema=lsp_type.CallHierarchyIncomingCallsResponse,
                file_paths=[file_path],
            ):
                calls.extend(resp)

        async with asyncer.create_task_group() as tg:
            for item in prepared:
                tg.soonify(request)(item)

        if calls:
            return calls

    async def request_call_hierarchy_outgoing_call(
        self, file_path: AnyPath, position: Position
    ) -> list[lsp_type.CallHierarchyOutgoingCall] | None:
        """
        Note: For symbol with multiple definitions, this method will return a list of
        all outgoing calls for each definition.
        """

        prepared = await self.prepare_call_hierarchy(file_path, position)

        if not prepared:
            return None

        calls: list[lsp_type.CallHierarchyOutgoingCall] = []

        async def append_calls(item: lsp_type.CallHierarchyItem) -> None:
            if resp := await self.file_request(
                req=lsp_type.CallHierarchyOutgoingCallsRequest(
                    id=jsonrpc_uuid(),
                    params=lsp_type.CallHierarchyOutgoingCallsParams(item=item),
                ),
                schema=lsp_type.CallHierarchyOutgoingCallsResponse,
                file_paths=[file_path],
            ):
                calls.extend(resp)

        async with asyncer.create_task_group() as tg:
            for item in prepared:
                tg.soonify(append_calls)(item)

        if calls:
            return calls
