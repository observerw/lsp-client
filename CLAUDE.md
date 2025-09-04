# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **full-featured, well-typed, and easy-to-use LSP client** library for Python that provides a high-level interface to interact with Language Server Protocol servers. The project supports multiple LSP servers (BasedPyright, Ty) and offers both synchronous and asynchronous capabilities.

## Architecture

### Core Components

- **LSPClient**: Abstract base class for LSP clients (`src/lsp_client/client/base.py:37`)
- **LSPServer**: Base class for LSP servers (`src/lsp_client/server/base.py:27`)
- **Capability System**: Modular capability groups for LSP features (`src/lsp_client/capability/`)
- **JSON-RPC**: Custom JSON-RPC implementation for LSP communication (`src/lsp_client/jsonrpc.py`)

### Key Design Patterns

- **Capability Groups**: Features are organized into composable capability groups (e.g., `FullFeaturedCapabilityGroup`, `WithRequestDocumentSymbols`)
- **Server-Specific Clients**: Concrete implementations like `BasedPyrightClient` and `TyClient` in `src/lsp_client/clients/`
- **Async Context Management**: Uses `asynccontextmanager` for proper resource cleanup
- **Type Safety**: Extensive use of Pydantic models and type hints with lsprotocol types

## Development Commands

### Setup

```bash
# Install dependencies
uv sync  # or: pip install -e .

# Install development dependencies
uv sync --group dev  # or: pip install -e ".[dev]"
```

### Linting & Formatting

```bash
# Run ruff linter
ruff check .

# Run ruff formatter
ruff format .

# Run mypy type checking
mypy src/
```

### Testing

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=lsp_client --cov-report=html

# Run async tests
pytest -p asyncio

# Run specific test
pytest tests/test_specific.py::test_function_name
```

### Examples

```bash
# Run BasedPyright example
python examples/run_basedpyright.py

# Run Ty example
python examples/run_ty.py

# Run symbols example
python examples/symbols.py
```

## Usage Patterns

### Basic Client Usage

```python
from pathlib import Path
from lsp_client.clients.based_pyright import BasedPyrightClient

async with BasedPyrightClient(workspace=Path("./my_project")) as client:
    # Find references
    refs = await client.request_references(
        file_path="main.py",
        position=Position(line=10, character=5)
    )

    # Get document symbols
    symbols = await client.request_document_symbols("main.py")
```

### Adding New LSP Server Support

1. Create server class inheriting from `LSPServer`
2. Create client class inheriting from `LSPClient[YourServer]`
3. Mix in appropriate capability groups
4. Implement required abstract methods

## Project Structure

```
src/lsp_client/
├── client/           # Client base classes and utilities
├── server/           # Server base classes and process management
├── capability/       # LSP capability groups and protocols
├── clients/          # Server-specific client implementations
└── utils/            # Shared utilities
```

## Key Files

- **Entry Points**: `src/lsp_client/__init__.py` - Main package exports
- **Core Abstractions**:
  - `src/lsp_client/client/base.py` - LSPClient base class
  - `src/lsp_client/server/base.py` - LSPServer base class
- **Capability Groups**: `src/lsp_client/capability/groups.py` - Feature mixins
- **JSON-RPC**: `src/lsp_client/jsonrpc.py` - Communication layer

## Important Conventions

- **Async First**: All operations are async/await based
- **Type Safety**: Use lsprotocol types for all LSP interactions
- **Resource Management**: Always use context managers for client/server lifecycle
- **Workspace Handling**: Supports both single-root and multi-root workspaces
- **File Synchronization**: Automatic file synchronization via `LSPFileBuffer`
