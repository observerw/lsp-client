from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

import asyncer

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import (
    CapabilityClientProtocol,
    TextDocumentCapabilityProtocol,
)
from lsp_client.utils.type_guard import is_completion_items
from lsp_client.utils.types import AnyPath, Position, lsp_type


@runtime_checkable
class WithRequestCompletion(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    - `textDocument/completion` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_completion
    - `completionItem/resolve` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#completionItem_resolve
    """

    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (
            lsp_type.TEXT_DOCUMENT_COMPLETION,
            lsp_type.COMPLETION_ITEM_RESOLVE,
        )

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        cap.completion = lsp_type.CompletionClientCapabilities(
            completion_item=lsp_type.ClientCompletionItemOptions(
                snippet_support=True,
                resolve_support=lsp_type.ClientCompletionItemResolveOptions(
                    properties=["documentation", "additionalTextEdits"]
                ),
            ),
            context_support=True,
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.completion_provider

    async def request_completion(
        self,
        file_path: AnyPath,
        position: Position,
        *,
        trigger_character: str | None = None,
        trigger_kind: lsp_type.CompletionTriggerKind = lsp_type.CompletionTriggerKind.Invoked,
        resolve: bool = False,
    ) -> Sequence[lsp_type.CompletionItem]:
        context = lsp_type.CompletionContext(
            trigger_kind=trigger_kind,
            trigger_character=trigger_character,
        )
        result = await self.file_request(
            lsp_type.CompletionRequest(
                id=jsonrpc_uuid(),
                params=lsp_type.CompletionParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                    context=context,
                ),
            ),
            schema=lsp_type.CompletionResponse,
            file_paths=[file_path],
        )

        match result:
            case lsp_type.CompletionList(items=items):
                res = list(items)
            case items if is_completion_items(items):
                res = list(items)
            case _:
                res = []

        if resolve and res:
            return await self.resolve_completion_items(res)
        return res

    async def resolve_completion_items(
        self,
        items: Sequence[lsp_type.CompletionItem],
    ) -> Sequence[lsp_type.CompletionItem]:
        async with asyncer.create_task_group() as tg:
            tasks = [
                tg.soonify(self.request_completion_resolve)(item) for item in items
            ]
        return [task.value for task in tasks]

    async def request_completion_resolve(
        self,
        item: lsp_type.CompletionItem,
    ) -> lsp_type.CompletionItem:
        return await self.request(
            lsp_type.CompletionResolveRequest(
                id=jsonrpc_uuid(),
                params=item,
            ),
            schema=lsp_type.CompletionResolveResponse,
        )
