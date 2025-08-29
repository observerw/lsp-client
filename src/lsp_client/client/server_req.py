from __future__ import annotations

import anyio
import lsprotocol.types as lsp_type
from loguru import logger
from lsprotocol import types

import lsp_client.capability as lsp_cap
from lsp_client import jsonrpc
from lsp_client.server import ServerRequest
from lsp_client.utils.channel import Receiver


class ServerRequestMixin:
    pending_timeout: float | None

    async def _dispatch_server_request(self, server_req: ServerRequest):
        match server_req:
            case {"method": types.WINDOW_LOG_MESSAGE} if isinstance(
                self, lsp_cap.WithReceiveLogMessage
            ):
                await self.receive_log_message(
                    jsonrpc.request_deserialize(
                        server_req, lsp_type.LogMessageNotification
                    )
                )
            case {"method": types.WINDOW_SHOW_MESSAGE} if isinstance(
                self, lsp_cap.WithReceiveShowMessage
            ):
                await self.receive_show_message(
                    jsonrpc.request_deserialize(
                        server_req, lsp_type.ShowMessageNotification
                    )
                )
            case ({"method": types.WINDOW_SHOW_MESSAGE_REQUEST} as raw_req, tx) if (
                isinstance(self, lsp_cap.WithRespondShowMessageRequest)
            ):
                resp = await self.respond_show_message(
                    jsonrpc.request_deserialize(raw_req, lsp_type.ShowMessageRequest)
                )
                tx.send(jsonrpc.response_serialize(resp))
            case {"method": types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS} if isinstance(
                self, lsp_cap.WithReceivePublishDiagnostics
            ):
                await self.receive_publish_diagnostics(
                    jsonrpc.request_deserialize(
                        server_req, lsp_type.PublishDiagnosticsNotification
                    )
                )
            case ({"method": types.WORKSPACE_WORKSPACE_FOLDERS} as raw_req, tx) if (
                isinstance(self, lsp_cap.WithRespondWorkspaceFolders)
            ):
                resp = await self.respond_workspace_folders(
                    jsonrpc.request_deserialize(
                        raw_req, lsp_type.WorkspaceFoldersRequest
                    )
                )
                tx.send(jsonrpc.response_serialize(resp))
            case (
                {"method": types.WORKSPACE_CONFIGURATION} as raw_req,
                tx,
            ) if isinstance(self, lsp_cap.WithRespondWorkspaceConfiguration):
                resp = await self.respond_workspace_configuration(
                    jsonrpc.request_deserialize(raw_req, lsp_type.ConfigurationRequest)
                )
                tx.send(jsonrpc.response_serialize(resp))
            case {"method": types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS} if isinstance(
                self, lsp_cap.WithReceivePublishDiagnostics
            ):
                await self.receive_publish_diagnostics(
                    jsonrpc.request_deserialize(
                        server_req, lsp_type.PublishDiagnosticsNotification
                    )
                )
            case (raw_req, _):
                # if server sent a request that client can't handle, raise an error
                raise ValueError(f"Unexpected server-side request: {raw_req}")
            case noti:
                logger.warning("Unknown notification: {}", noti)

    async def _server_request_worker(self, receiver: Receiver[ServerRequest]):
        """
        This worker will gracefully shutdown after:
            - All server-side requests are received, indicated by receive() return None
            - All received requests are dispatched and handled, indicated by TaskGroup exit
        """

        async def _dispatch_with_timeout(server_req: ServerRequest):
            with anyio.fail_after(self.pending_timeout):
                await self._dispatch_server_request(server_req)

        async with anyio.create_task_group() as tg:
            async for server_req in receiver:
                tg.start_soon(_dispatch_with_timeout, server_req)
