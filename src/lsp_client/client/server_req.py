from __future__ import annotations

import asyncio as aio
from dataclasses import dataclass
from typing import Protocol

from lsprotocol import types

import lsp_client.capability as cap
from lsp_client.jsonrpc import (
    JsonRpcRawReqPackage,
    JsonRpcResponse,
    lsp_converter,
)
from lsp_client.server import ServerRequestQueue


@dataclass
class ServerRequestClient(cap.LSPCapabilityClient, Protocol):
    """Client mixin for handling server-side requests."""

    server_req_queue: ServerRequestQueue
    """Server-side request"""

    async def process_notification(self, coro: aio._CoroutineLike[None]):
        await coro
        self.server_req_queue.task_done()

    async def process_request(self, coro: aio._CoroutineLike[JsonRpcResponse]):
        # should be and response or `types.ResponseErrorMessage`
        resp = await coro
        await self.respond(resp)
        self.server_req_queue.task_done()

    async def handle_server_request(self, raw_req: JsonRpcRawReqPackage):
        match raw_req:
            case {"method": types.WINDOW_LOG_MESSAGE} if isinstance(
                self, cap.WithReceiveLogMessage
            ):
                req = lsp_converter.structure(raw_req, types.LogMessageNotification)
                await self.process_notification(self.receive_log_message(req))
            case {"method": types.WINDOW_SHOW_MESSAGE} if isinstance(
                self, cap.WithReceiveShowMessage
            ):
                req = lsp_converter.structure(raw_req, types.ShowMessageNotification)
                await self.process_notification(self.receive_show_message(req))
            case {"method": types.WINDOW_SHOW_MESSAGE_REQUEST} if isinstance(
                self, cap.WithRespondShowMessage
            ):
                req = lsp_converter.structure(raw_req, types.ShowMessageRequest)
                await self.process_request(self.respond_show_message(req))
            case {"method": types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS} if isinstance(
                self, cap.WithNotifyPublishDiagnostics
            ):
                req = lsp_converter.structure(
                    raw_req, types.PublishDiagnosticsNotification
                )
                await self.process_notification(self.notify_publish_diagnostics(req))
            # TODO add more server request handlers here
            case other_req:
                self.logger.warning(
                    "Received unhandled server request: %s",
                    other_req,
                )
                self.server_req_queue.task_done()

    async def _server_req_worker(self):
        """Worker to handle server side requests."""

        async with aio.TaskGroup() as tg:
            while True:
                raw_req = await self.server_req_queue.get()
                tg.create_task(self.handle_server_request(raw_req))
