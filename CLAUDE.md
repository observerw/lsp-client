# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an LSP (Language Server Protocol) client library for Python that provides a full-featured, well-typed, and easy-to-use interface for communicating with LSP servers. The project enables parallel processing with multiple server instances and supports various LSP capabilities like references, definitions, hover information, and more.

## Key Commands

### Development Setup

- `uv sync` - Install dependencies
- `uv sync --group dev` - Install with development dependencies
- `uv sync --group mcp` - Install with MCP dependencies

### Testing

- `pytest` - Run all tests
- `pytest tests/test_basic.py` - Run specific test file
- `pytest -v` - Run tests with verbose output

### Code Quality

- `ruff check` - Lint code
- `ruff format` - Format code
- `ruff check --fix` - Auto-fix linting issues
- `mypy src/` - Type checking

### Build and Release

- `just bump version="x.x.x"` - Bump version and create git tag

## Architecture

### Core Components

**LSPClientBase** (`src/lsp_client/client/base.py`): The foundational client class that manages:

- Server pool connections and load balancing
- File buffer management for document synchronization
- Request/response handling with asyncio task groups
- Context management for proper server lifecycle

**Capability System** (`src/lsp_client/capability/`): Protocol-based capability definitions that allow:

- Modular LSP feature composition using mixins
- Type-safe capability checking at class definition time
- Custom capability implementations for specific servers

**Server Pool** (`src/lsp_client/server/`): Multi-process server management:

- Parallel LSP server instances for improved performance
- Automatic load balancing across server processes
- Request queuing and response correlation

**LSP Server Implementations** (`src/lsp_client/servers/`): Pre-configured clients for specific servers:

- `BasedPyrightClient`: Python language server with comprehensive capabilities
- Extensible pattern for adding new server support

**MCP Integration** (`src/lsp_client/mcp/`): MCP server implementation:

- `cli.py`: CLI interface for MCP tools
- `locate.py`: Location resolution utilities

### Key Design Patterns

**Protocol-Based Capabilities**: LSP features are implemented as Protocol classes that can be mixed into client implementations. This allows for:

- Type-safe capability composition
- Runtime capability checking
- Easy extension for new LSP features

**Async Context Management**: The client uses async context managers for:

- Proper server lifecycle management (start/shutdown/exit)
- File opening/closing with document synchronization
- Resource cleanup on errors or completion

**Multi-Server Architecture**: The server pool pattern enables:

- Parallel request processing across multiple server instances
- Load balancing for improved performance on large codebases
- Fault isolation between server processes

### File Structure

- `src/lsp_client/client/`: Core client implementation and file buffer management
- `src/lsp_client/capability/`: Protocol definitions for LSP capabilities
- `src/lsp_client/server/`: Server process management and request handling
- `src/lsp_client/servers/`: Concrete server implementations
- `src/lsp_client/utils/`: Path utilities and helper functions
- `src/lsp_client/mcp/`: MCP server tools and utilities
- `tests/`: Test suite including mock server for testing

## Usage Patterns

### Basic Client Usage

```python
async with BasedPyrightClient.start(repo_path=".", server_count=4) as client:
    refs = await client.request_references(file_path="file.py", position=Position(10, 5))
```

### Parallel Request Processing

```python
tasks = [
    client.create_request(client.request_definition(file, pos))
    for file, pos in file_positions
]
results = [task.result() for task in tasks]
```

### MCP Server Usage

```bash
lsp-client --repo-path /path/to/repo
```

### Custom Server Implementation

Extend `LSPClientBase` with desired capability mixins and provide:

- `language_id`: Target language
- `server_cmd`: Command to start the LSP server
- `client_capabilities`: LSP client capabilities declaration

## Development Notes

- Python 3.13+ required
- Uses `ruff` for linting with comprehensive rule set
- Enforces `from __future__ import annotations` imports
- Type hints are mandatory throughout the codebase
- Async/await pattern used extensively for LSP communication
