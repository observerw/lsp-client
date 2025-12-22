from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Literal

import anyio
from loguru import logger
from pydantic import BaseModel, Field

SOCKET_PATH = Path("/tmp/lsp_client_daemon.sock")


class ServerInfo(BaseModel):
    image: str
    status: str = "running"


class CreateParams(BaseModel):
    name: str
    image: str


class StopParams(BaseModel):
    name: str


class ListParams(BaseModel): ...


class DaemonRequest(BaseModel):
    command: Literal["create", "list", "stop"]
    params: CreateParams | StopParams | ListParams = Field(default_factory=ListParams)


class DaemonResponse(BaseModel):
    status: str
    message: str | None = None
    servers: dict[str, ServerInfo] | None = None


class Daemon:
    def __init__(self):
        self.servers: dict[str, ServerInfo] = {}

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        try:
            data = await reader.read(4096)
            if not data:
                return

            request = DaemonRequest.model_validate_json(data.decode())

            response = await self.process_command(request)
            writer.write(response.model_dump_json().encode())
            await writer.drain()
        except Exception as e:
            logger.error(f"Error handling client: {e}")
            error_response = DaemonResponse(status="error", message=str(e))
            writer.write(error_response.model_dump_json().encode())
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def process_command(self, request: DaemonRequest) -> DaemonResponse:
        params = request.params
        match request.command:
            case "create":
                if not isinstance(params, CreateParams):
                    return DaemonResponse(
                        status="error", message="Invalid parameters for create"
                    )
                name = params.name
                image = params.image

                if name in self.servers:
                    return DaemonResponse(
                        status="error", message=f"Server {name} already exists"
                    )

                self.servers[name] = ServerInfo(image=image)
                return DaemonResponse(
                    status="success",
                    message=f"Server {name} created with image {image}",
                )

            case "list":
                return DaemonResponse(status="success", servers=self.servers)

            case "stop":
                if not isinstance(params, StopParams):
                    return DaemonResponse(
                        status="error", message="Invalid parameters for stop"
                    )
                name = params.name
                if name not in self.servers:
                    return DaemonResponse(
                        status="error", message=f"Server {name} not found"
                    )

                del self.servers[name]
                return DaemonResponse(
                    status="success", message=f"Server {name} stopped"
                )

            case _:
                return DaemonResponse(
                    status="error", message=f"Unknown command: {request.command}"
                )

    async def run(self):
        if SOCKET_PATH.exists():
            SOCKET_PATH.unlink()

        server = await asyncio.start_unix_server(
            self.handle_client, path=str(SOCKET_PATH)
        )
        async with server:
            await server.serve_forever()


if __name__ == "__main__":
    daemon = Daemon()
    anyio.run(daemon.run)
