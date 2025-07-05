"""
Example usage of the MockLSPServer for testing.

This file demonstrates how to use the MockLSPServer with different configurations
to test LSP client functionality.
"""

from __future__ import annotations

from lsprotocol import types

from tests.mock_server.mock_server import (
    MockLSPServer,
    create_completion_mock_server,
    create_definition_mock_server,
    create_hover_mock_server,
)


async def test_basic_mock_server():
    """Test a basic mock server with default capabilities."""
    print("=== Testing Basic Mock Server ===")

    # Create a mock server with default capabilities
    server = MockLSPServer()

    # Customize some responses
    server.add_static_responses(
        {
            "textDocument/hover": {
                "contents": {
                    "kind": "markdown",
                    "value": "This is a **mock** hover response!",
                }
            }
        }
    )

    print(f"Server capabilities: {server.server_capabilities}")
    print("Mock server configured successfully!")


async def test_completion_mock_server():
    """Test a mock server that provides code completion."""
    print("\n=== Testing Completion Mock Server ===")

    # Create a mock server for completion
    server = create_completion_mock_server(
        completion_items=["mock_function", "mock_variable", "mock_class", "mock_method"]
    )

    # Simulate a completion request
    completion_response = server._generate_response(
        "textDocument/completion",
        {
            "textDocument": {"uri": "file:///test.py"},
            "position": {"line": 10, "character": 5},
        },
    )

    print(f"Completion response: {completion_response}")


async def test_hover_mock_server():
    """Test a mock server that provides hover information."""
    print("\n=== Testing Hover Mock Server ===")

    # Create a mock server for hover
    server = create_hover_mock_server(
        "# Custom Hover Content\n\nThis is a custom hover message!"
    )

    # Simulate a hover request
    hover_response = server._generate_response(
        "textDocument/hover",
        {
            "textDocument": {"uri": "file:///test.py"},
            "position": {"line": 5, "character": 10},
        },
    )

    print(f"Hover response: {hover_response}")


async def test_definition_mock_server():
    """Test a mock server that provides go-to-definition."""
    print("\n=== Testing Definition Mock Server ===")

    # Create a mock server for definition
    server = create_definition_mock_server("file:///mock/definition.py")

    # Simulate a definition request
    definition_response = server._generate_response(
        "textDocument/definition",
        {
            "textDocument": {"uri": "file:///test.py"},
            "position": {"line": 15, "character": 20},
        },
    )

    print(f"Definition response: {definition_response}")


async def test_custom_capabilities():
    """Test a mock server with custom capabilities."""
    print("\n=== Testing Custom Capabilities ===")

    # Create a mock server with custom capabilities
    custom_capabilities = types.ServerCapabilities(
        text_document_sync=types.TextDocumentSyncOptions(
            open_close=True,
            change=types.TextDocumentSyncKind.Incremental,
        ),
        hover_provider=True,
        completion_provider=types.CompletionOptions(
            trigger_characters=[".", "->", "::"],
            resolve_provider=False,
        ),
        definition_provider=True,
        references_provider=True,
        # Add more capabilities as needed
        code_action_provider=types.CodeActionOptions(
            code_action_kinds=[
                types.CodeActionKind.QuickFix,
                types.CodeActionKind.Refactor,
            ]
        ),
    )

    server = MockLSPServer(server_capabilities=custom_capabilities)

    # Add custom response handlers
    def handle_code_action(method: str, params: dict | None) -> list[dict]:
        if params is None:
            return []

        return [
            {
                "title": "Fix spelling",
                "kind": types.CodeActionKind.QuickFix,
                "edit": {
                    "changes": {
                        params["textDocument"]["uri"]: [
                            {"range": params["range"], "newText": "corrected_text"}
                        ]
                    }
                },
            }
        ]

    server.add_callback_responses({"textDocument/codeAction": handle_code_action})

    # Test the custom code action
    code_action_response = server._generate_response(
        "textDocument/codeAction",
        {
            "textDocument": {"uri": "file:///test.py"},
            "range": {
                "start": {"line": 1, "character": 0},
                "end": {"line": 1, "character": 10},
            },
            "context": {"diagnostics": [], "only": [types.CodeActionKind.QuickFix]},
        },
    )

    print(f"Code action response: {code_action_response}")


async def test_message_flow():
    """Test the complete message flow simulation."""
    print("\n=== Testing Message Flow ===")

    server = MockLSPServer()

    # Simulate initialize request
    init_response = server._generate_response(
        "initialize",
        {
            "processId": 12345,
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
            "capabilities": {},
        },
    )

    print(f"Initialize response: {init_response}")

    # Simulate textDocument/didOpen notification
    server._generate_response(
        "textDocument/didOpen",
        {
            "textDocument": {
                "uri": "file:///test.py",
                "languageId": "python",
                "version": 1,
                "text": "def hello():\n    print('Hello, World!')",
            }
        },
    )

    print("File opened successfully")
    print(f"Tracked documents: {list(server._text_documents.keys())}")

    # Simulate shutdown
    shutdown_response = server._generate_response("shutdown", None)
    print(f"Shutdown response: {shutdown_response}")
    print(f"Shutdown requested: {server._shutdown_requested}")


async def main():
    """Run all tests."""
    print("Testing MockLSPServer Implementation")
    print("=" * 50)

    await test_basic_mock_server()
    await test_completion_mock_server()
    await test_hover_mock_server()
    await test_definition_mock_server()
    await test_custom_capabilities()
    await test_message_flow()

    print("\n" + "=" * 50)
    print("All tests completed successfully!")
