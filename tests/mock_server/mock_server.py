#!/usr/bin/env python3
"""
Mock LSP Server for testing purposes.

This module provides a MockLSPServer that can be configured with custom capabilities
and mock responses to facilitate testing of LSP clients.
"""

from __future__ import annotations

import asyncio as aio
import json
import logging
import re
import sys
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from lsprotocol import converters, types

# Type aliases for better readability
type MockResponseGenerator = Callable[[dict[str, Any]], dict[str, Any]]
type RequestHandler = Callable[[str, dict[str, Any] | None], Any]

logger = logging.getLogger(__name__)

# Get the LSP converter for serialization
lsp_converter = converters.get_converter()


class MockResponseProvider(ABC):
    """Abstract base class for providing mock responses to LSP requests."""

    @abstractmethod
    def can_handle(self, method: str) -> bool:
        """Check if this provider can handle the given method."""

    @abstractmethod
    def generate_response(self, method: str, params: dict[str, Any] | None) -> Any:
        """Generate a mock response for the given method and parameters."""


@dataclass
class StaticResponseProvider(MockResponseProvider):
    """A response provider that returns predefined static responses."""

    responses: Mapping[str, dict[str, Any]] = field(default_factory=dict)

    def can_handle(self, method: str) -> bool:
        return method in self.responses

    def generate_response(self, method: str, params: dict[str, Any] | None) -> Any:
        return self.responses.get(method)


@dataclass
class CallbackResponseProvider(MockResponseProvider):
    """A response provider that uses callback functions to generate responses."""

    callbacks: Mapping[str, RequestHandler] = field(default_factory=dict)

    def can_handle(self, method: str) -> bool:
        return method in self.callbacks

    def generate_response(self, method: str, params: dict[str, Any] | None) -> Any:
        if callback := self.callbacks.get(method):
            return callback(method, params)
        return None


@dataclass
class MockLSPServer:
    """
    A mock LSP server for testing purposes.

    This server can be configured with custom server capabilities and mock response providers
    to simulate various LSP server behaviors during testing.
    """

    # Default server capabilities - can be overridden
    server_capabilities: types.ServerCapabilities = field(
        default_factory=lambda: types.ServerCapabilities(
            text_document_sync=types.TextDocumentSyncOptions(
                open_close=True,
                change=types.TextDocumentSyncKind.Full,
                save=types.SaveOptions(include_text=True),
            ),
            hover_provider=True,
            completion_provider=types.CompletionOptions(
                trigger_characters=["."],
                resolve_provider=True,
            ),
            definition_provider=True,
            references_provider=True,
            document_symbol_provider=True,
            workspace_symbol_provider=True,
            code_action_provider=True,
            code_lens_provider=types.CodeLensOptions(resolve_provider=True),
            document_formatting_provider=True,
            document_range_formatting_provider=True,
            rename_provider=types.RenameOptions(prepare_provider=True),
            folding_range_provider=True,
            semantic_tokens_provider=types.SemanticTokensOptions(
                legend=types.SemanticTokensLegend(
                    token_types=["keyword", "string", "comment"],
                    token_modifiers=["declaration", "definition"],
                ),
                range=True,
                full=True,
            ),
        )
    )

    # Response providers for handling different types of requests
    response_providers: list[MockResponseProvider] = field(default_factory=list)

    # Server info
    server_info: types.ServerInfo = field(
        default_factory=lambda: types.ServerInfo(
            name="MockLSPServer",
            version="1.0.0",
        )
    )

    # Internal state
    _initialized: bool = field(default=False, init=False)
    _shutdown_requested: bool = field(default=False, init=False)
    _text_documents: dict[str, str] = field(default_factory=dict, init=False)

    def __post_init__(self):
        self.logger = logging.getLogger("MockLSPServer")

        # Add default response providers for standard LSP methods
        self._add_default_providers()

    def _add_default_providers(self):
        """Add default response providers for common LSP methods."""

        # Initialize response provider
        def handle_initialize(
            method: str, params: dict[str, Any] | None
        ) -> dict[str, Any]:
            self._initialized = True
            return {
                "capabilities": lsp_converter.unstructure(self.server_capabilities),
                "serverInfo": lsp_converter.unstructure(self.server_info),
            }

        # Shutdown response provider
        def handle_shutdown(
            method: str, params: dict[str, Any] | None
        ) -> dict[str, Any] | None:
            self._shutdown_requested = True
            return None

        # Text document synchronization providers
        def handle_did_open(
            method: str, params: dict[str, Any] | None
        ) -> dict[str, Any] | None:
            if params and "textDocument" in params:
                text_doc = params["textDocument"]
                self._text_documents[text_doc["uri"]] = text_doc.get("text", "")
            return None

        def handle_did_change(
            method: str, params: dict[str, Any] | None
        ) -> dict[str, Any] | None:
            if params and "textDocument" in params and "contentChanges" in params:
                uri = params["textDocument"]["uri"]
                # Handle full document sync (assuming TextDocumentSyncKind.Full)
                if params["contentChanges"]:
                    self._text_documents[uri] = params["contentChanges"][-1].get(
                        "text", ""
                    )
            return None

        def handle_did_close(
            method: str, params: dict[str, Any] | None
        ) -> dict[str, Any] | None:
            if params and "textDocument" in params:
                uri = params["textDocument"]["uri"]
                self._text_documents.pop(uri, None)
            return None

        # Add default providers
        default_callbacks = {
            "initialize": handle_initialize,
            "shutdown": handle_shutdown,
            "textDocument/didOpen": handle_did_open,
            "textDocument/didChange": handle_did_change,
            "textDocument/didClose": handle_did_close,
        }

        self.response_providers.append(
            CallbackResponseProvider(callbacks=default_callbacks)
        )

    def add_response_provider(self, provider: MockResponseProvider) -> None:
        """Add a custom response provider."""
        self.response_providers.append(provider)

    def add_static_responses(self, responses: Mapping[str, dict[str, Any]]) -> None:
        """Add static responses for specific methods."""
        self.add_response_provider(StaticResponseProvider(responses=responses))

    def add_callback_responses(self, callbacks: Mapping[str, RequestHandler]) -> None:
        """Add callback-based responses for specific methods."""
        self.add_response_provider(CallbackResponseProvider(callbacks=callbacks))

    def _generate_response(self, method: str, params: dict[str, Any] | None) -> Any:
        """Generate a response for the given method and parameters."""
        for provider in self.response_providers:
            if provider.can_handle(method):
                return provider.generate_response(method, params)

        # Default fallback for unknown methods
        self.logger.warning(f"No response provider found for method: {method}")
        return {"error": f"Method not supported: {method}"}

    def _create_response_message(
        self, request_id: str | int | None, result: Any
    ) -> dict[str, Any]:
        """Create a JSON-RPC response message."""
        response: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
        }

        if result is None:
            response["result"] = None
        elif isinstance(result, dict) and "error" in result:
            response["error"] = {
                "code": -32601,  # Method not found
                "message": result["error"],
            }
        else:
            response["result"] = result

        return response

    def _send_notification(
        self, method: str, params: dict[str, Any] | None = None
    ) -> None:
        """Send a notification to the client."""
        notification: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params:
            notification["params"] = params

        self._write_message(notification)

    def _write_message(self, message: dict[str, Any]) -> None:
        """Write a message to stdout using LSP protocol format."""
        content = json.dumps(message, separators=(",", ":"))
        content_bytes = content.encode("utf-8")
        header = f"Content-Length: {len(content_bytes)}\r\n\r\n"

        sys.stdout.buffer.write(header.encode("utf-8"))
        sys.stdout.buffer.write(content_bytes)
        sys.stdout.buffer.flush()

    async def _read_message(self) -> dict[str, Any] | None:
        """Read a message from stdin using LSP protocol format."""
        try:
            # Read header
            header_line = await aio.get_event_loop().run_in_executor(
                None, sys.stdin.buffer.readline
            )

            if not header_line:
                return None  # EOF

            header = header_line.decode("utf-8")
            match = re.match(r"Content-Length:\s*(\d+)\r\n", header)

            if not match:
                self.logger.error(f"Invalid header: {header}")
                return None

            content_length = int(match.group(1))

            # Read empty line
            await aio.get_event_loop().run_in_executor(None, sys.stdin.buffer.readline)

            # Read content
            content_bytes = await aio.get_event_loop().run_in_executor(
                None, sys.stdin.buffer.read, content_length
            )

            content = content_bytes.decode("utf-8")
            return json.loads(content)

        except Exception as e:
            self.logger.error(f"Error reading message: {e}")
            return None

    async def _handle_request(self, message: dict[str, Any]) -> None:
        """Handle an incoming request message."""
        method = message.get("method")
        params = message.get("params")
        request_id = message.get("id")

        if method is None:
            self.logger.error("Received message without method")
            return

        self.logger.debug(f"Handling request: {method} (id: {request_id})")

        # Generate response
        result = self._generate_response(method, params)

        # Send response (only for requests, not notifications)
        if request_id is not None:
            response = self._create_response_message(request_id, result)
            self._write_message(response)

    async def run(self) -> None:
        """Run the mock LSP server."""
        self.logger.info("Starting MockLSPServer")

        try:
            while not self._shutdown_requested:
                message = await self._read_message()

                if message is None:
                    break  # EOF or error

                await self._handle_request(message)

        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Error in server loop: {e}")
        finally:
            self.logger.info("MockLSPServer shutting down")


# Utility functions for creating mock servers with common configurations


def create_hover_mock_server(
    hover_content: str = "Mock hover content",
) -> MockLSPServer:
    """Create a mock server that provides hover information."""
    server = MockLSPServer()

    def handle_hover(method: str, params: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "contents": {
                "kind": "markdown",
                "value": hover_content,
            }
        }

    server.add_callback_responses({"textDocument/hover": handle_hover})
    return server


def create_completion_mock_server(
    completion_items: list[str] | None = None,
) -> MockLSPServer:
    """Create a mock server that provides code completion."""
    if completion_items is None:
        completion_items = ["mock_function", "mock_variable", "mock_class"]

    server = MockLSPServer()

    def handle_completion(method: str, params: dict[str, Any] | None) -> dict[str, Any]:
        items = [
            {
                "label": item,
                "kind": 3,  # Function
                "detail": f"Mock completion for {item}",
                "insertText": item,
            }
            for item in completion_items
        ]
        return {"items": items}

    server.add_callback_responses({"textDocument/completion": handle_completion})
    return server


def create_definition_mock_server(
    definition_uri: str = "file:///mock/definition.py",
) -> MockLSPServer:
    """Create a mock server that provides go-to-definition."""
    server = MockLSPServer()

    def handle_definition(
        method: str, params: dict[str, Any] | None
    ) -> list[dict[str, Any]]:
        return [
            {
                "uri": definition_uri,
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 0, "character": 10},
                },
            }
        ]

    server.add_callback_responses({"textDocument/definition": handle_definition})
    return server


# CLI interface for running the mock server
async def main():
    """Main entry point for running the mock server from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Mock LSP Server for testing")
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    parser.add_argument("--config", help="Path to configuration file (JSON)")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr)
        ],  # Log to stderr to avoid interfering with LSP protocol
    )

    # Create server
    server = MockLSPServer()

    # Load configuration if provided
    if args.config:
        with open(args.config) as f:
            config = json.load(f)

        # Apply configuration (simplified example)
        if "responses" in config:
            server.add_static_responses(config["responses"])

    # Run server
    await server.run()


if __name__ == "__main__":
    aio.run(main())
