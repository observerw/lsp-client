#!/usr/bin/env python3
"""
Example of running the MockLSPServer as a standalone LSP server process.

This script demonstrates how to use the MockLSPServer to act as a real LSP server
that can be connected to by LSP clients.
"""
from __future__ import annotations

import asyncio as aio
import sys
from pathlib import Path

from lsprotocol import types

# Add the parent directory to the path to import mock_server
sys.path.insert(0, str(Path(__file__).parent))

from tests.mock_server.mock_server import MockLSPServer


async def run_mock_server():
    """Run a configured mock LSP server."""

    # Create a mock server with comprehensive capabilities
    server = MockLSPServer(
        server_capabilities=types.ServerCapabilities(
            text_document_sync=types.TextDocumentSyncOptions(
                open_close=True,
                change=types.TextDocumentSyncKind.Full,
                save=types.SaveOptions(include_text=True),
            ),
            hover_provider=True,
            completion_provider=types.CompletionOptions(
                trigger_characters=[".", "->", "::"],
                resolve_provider=True,
            ),
            definition_provider=True,
            references_provider=True,
            document_symbol_provider=True,
            code_action_provider=True,
            diagnostic_provider=types.DiagnosticOptions(
                identifier="mock-lsp",
                inter_file_dependencies=True,
                workspace_diagnostics=True,
            ),
        ),
        server_info=types.ServerInfo(
            name="MockLSPServer",
            version="1.0.0",
        ),
    )

    # Configure custom responses for common LSP methods

    # Hover provider
    def handle_hover(method: str, params: dict | None) -> dict:
        if not params:
            return {
                "contents": {
                    "kind": "markdown",
                    "value": "No hover information available",
                }
            }

        # Extract position info
        position = params.get("position", {})
        line = position.get("line", 0)
        character = position.get("character", 0)

        return {
            "contents": {
                "kind": "markdown",
                "value": f"**Mock Hover Information**\n\nPosition: Line {line}, Character {character}\n\nThis is a mock hover response from the MockLSPServer!",
            }
        }

    # Completion provider
    def handle_completion(method: str, params: dict | None) -> dict:
        if not params:
            return {"items": []}

        # Extract context
        text_doc = params.get("textDocument", {})
        uri = text_doc.get("uri", "")

        # Mock completion items based on file type
        if uri.endswith(".py"):
            items = [
                {
                    "label": "mock_function",
                    "kind": types.CompletionItemKind.Function,
                    "detail": "Mock Python function",
                    "insertText": "mock_function()",
                    "documentation": "A mock Python function for testing",
                },
                {
                    "label": "mock_class",
                    "kind": types.CompletionItemKind.Class,
                    "detail": "Mock Python class",
                    "insertText": "MockClass",
                    "documentation": "A mock Python class for testing",
                },
                {
                    "label": "mock_variable",
                    "kind": types.CompletionItemKind.Variable,
                    "detail": "Mock Python variable",
                    "insertText": "mock_variable",
                    "documentation": "A mock Python variable for testing",
                },
            ]
        else:
            items = [
                {
                    "label": "mock_item",
                    "kind": types.CompletionItemKind.Text,
                    "detail": "Mock completion item",
                    "insertText": "mock_item",
                    "documentation": "A generic mock completion item",
                }
            ]

        return {"items": items}

    # Definition provider
    def handle_definition(method: str, params: dict | None) -> list[dict]:
        if not params:
            return []

        text_doc = params.get("textDocument", {})
        uri = text_doc.get("uri", "")

        # Mock definition location
        return [
            {
                "uri": uri,
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 0, "character": 10},
                },
            }
        ]

    # References provider
    def handle_references(method: str, params: dict | None) -> list[dict]:
        if not params:
            return []

        text_doc = params.get("textDocument", {})
        uri = text_doc.get("uri", "")
        position = params.get("position", {})

        # Mock multiple references
        return [
            {
                "uri": uri,
                "range": {
                    "start": {
                        "line": position.get("line", 0),
                        "character": position.get("character", 0),
                    },
                    "end": {
                        "line": position.get("line", 0),
                        "character": position.get("character", 0) + 10,
                    },
                },
            },
            {
                "uri": uri,
                "range": {
                    "start": {"line": position.get("line", 0) + 5, "character": 0},
                    "end": {"line": position.get("line", 0) + 5, "character": 10},
                },
            },
        ]

    # Document symbols provider
    def handle_document_symbols(method: str, params: dict | None) -> list[dict]:
        if not params:
            return []

        # Mock document symbols
        return [
            {
                "name": "MockClass",
                "detail": "A mock class",
                "kind": types.SymbolKind.Class,
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 10, "character": 0},
                },
                "selectionRange": {
                    "start": {"line": 0, "character": 6},
                    "end": {"line": 0, "character": 15},
                },
            },
            {
                "name": "mock_function",
                "detail": "A mock function",
                "kind": types.SymbolKind.Function,
                "range": {
                    "start": {"line": 2, "character": 4},
                    "end": {"line": 5, "character": 4},
                },
                "selectionRange": {
                    "start": {"line": 2, "character": 8},
                    "end": {"line": 2, "character": 21},
                },
            },
        ]

    # Code actions provider
    def handle_code_actions(method: str, params: dict | None) -> list[dict]:
        if not params:
            return []

        return [
            {
                "title": "Add mock import",
                "kind": types.CodeActionKind.QuickFix,
                "edit": {
                    "changes": {
                        params["textDocument"]["uri"]: [
                            {
                                "range": {
                                    "start": {"line": 0, "character": 0},
                                    "end": {"line": 0, "character": 0},
                                },
                                "newText": "from unittest.mock import Mock\n",
                            }
                        ]
                    }
                },
            },
            {
                "title": "Generate mock test",
                "kind": types.CodeActionKind.Refactor,
                "edit": {
                    "changes": {
                        params["textDocument"]["uri"]: [
                            {
                                "range": params["range"],
                                "newText": "def test_mock():\n    mock = Mock()\n    assert mock is not None",
                            }
                        ]
                    }
                },
            },
        ]

    # Register all the custom handlers
    server.add_callback_responses(
        {
            "textDocument/hover": handle_hover,
            "textDocument/completion": handle_completion,
            "textDocument/definition": handle_definition,
            "textDocument/references": handle_references,
            "textDocument/documentSymbol": handle_document_symbols,
            "textDocument/codeAction": handle_code_actions,
        }
    )

    # Run the server
    await server.run()


if __name__ == "__main__":
    # This script can be used as a standalone LSP server
    # Example usage:
    # python mock_server_example.py

    print("Starting MockLSPServer...", file=sys.stderr)
    print("Server is ready to accept LSP connections.", file=sys.stderr)

    try:
        aio.run(run_mock_server())
    except KeyboardInterrupt:
        print("MockLSPServer stopped by user.", file=sys.stderr)
    except Exception as e:
        print(f"MockLSPServer error: {e}", file=sys.stderr)
        sys.exit(1)
