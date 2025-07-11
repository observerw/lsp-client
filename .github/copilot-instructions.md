# LSP Client Development Guide

A high-quality, type-safe, parallelization-enabled Python LSP client library. Built on `multilspy` principles with better type hints and simpler extensibility.

## 🏗️ Core Architecture

### Capability-Based Component System

- **Mixin Design Pattern**: Uses `Protocol` type-checked capability mixins (e.g., `WithRequestReferences`, `WithRequestDefinition`)
- **Composition Over Inheritance**: LSP clients gain functionality by composing multiple capability classes
- **Type-Safe Protocols**: Uses `@runtime_checkable` Protocol for compile-time type checking

```python
# Example: Composing multiple capabilities
class MyClient(
    cap.WithRequestReferences,
    cap.WithRequestDefinition, 
    LSPClientBase,
): ...
```

### Multi-Process Server Pool Architecture

- **LSPServerPool**: Manages multiple parallel LSP server processes with random load balancing
- **Async Communication**: Fully asyncio-based using JSON-RPC over stdio
- **Graceful Shutdown**: Supports timeout-controlled server process lifecycle management

## 🔧 Development Workflow

### Project Setup

```bash
uv sync                    # Install dependencies
uv run python examples/basic.py  # Run examples
```

### Testing & Debugging

- **Mock Server**: `tests/mock_server/` provides complete LSP server simulation
- **Test Execution**: `uv run pytest`
- **Standalone Mock Server**: `python tests/mock_server/mock_server.py --config config.json`

### Version Release

- Use `justfile` for automated version releases: `just bump 1.0.0`

## 🛠️ Adding New LSP Servers

Follow the `src/lsp_client/servers/based_pyright.py` pattern:

```python
class NewServerClient(
    cap.WithRequestReferences,  # Add required capabilities
    cap.WithRequestDefinition,
    LSPClientBase,
):
    language_id: ClassVar = types.LanguageKind.YourLanguage
    server_cmd: ClassVar = ("your-lsp-server", "--stdio")
    client_capabilities: ClassVar[types.ClientCapabilities] = ...
```

**Key Points**:

- Must inherit from `LSPClientBase`
- Only add capabilities actually supported by the server
- `server_cmd` must launch server in stdio mode

## 🔌 Extending New Capabilities

1. **Create capability mixin**: Define in `src/lsp_client/capability/`
2. **Implement protocol methods**: Follow LSP specification for request/response formats
3. **Add type checking**: Use `check_client_capability()` and `check_server_capability()`

## 📊 Performance Optimization Patterns

### Parallel Request Processing

```python
# Use TaskGroup-like interface for parallel requests
tasks = [
    client.create_request(client.request_references(file, pos))
    for file, pos in file_position_pairs
]
results = [task.result() for task in tasks]
```

### File Buffer Management

- Use `client.open_files()` context manager for automatic document synchronization
- LSPFileBuffer automatically manages `textDocument/didOpen` and `didClose` lifecycle

## 📁 Key File Structure

```text
src/lsp_client/
├── capability/          # LSP capability mixins
│   ├── request.py       # Client request capabilities 
│   ├── notification.py  # Notification capabilities
│   └── response.py      # Server response capabilities
├── client/
│   ├── base.py         # LSPClientBase core implementation
│   ├── server_req.py   # Server-side request handling
│   └── buffer.py       # File buffer management
├── server/
│   ├── base.py         # LSPServerPool management
│   ├── process.py      # Individual server process
│   └── event.py        # Request/response event management
└── servers/            # Specific LSP server implementations
```

## ⚠️ Common Pitfalls

- **Don't instantiate clients directly**: Always use `async with Client.start()`
- **Capability checking**: Ensure implementing `check_client_capability()` when adding new capabilities
- **Server process count**: Avoid starting too many processes that could exhaust system resources, adjust `server_count` based on system capabilities
- **Async context**: All LSP operations must be performed within async context

## 🔍 Debugging Tips

- **Logging configuration**: Use `logging.getLogger("lsp_client")` to view detailed communication logs
- **Mock testing**: Use `tests/mock_server/` to simulate various server response scenarios
- **Process monitoring**: LSPServerProcess provides detailed process lifecycle logging

## 📋 Code Conventions

- **Type hints**: Strict use of type hints, especially `ClassVar` for class-level configuration
- **Async-first**: All I/O operations use async/await
- **Error handling**: Use LSP standard error response formats
- **Docstrings**: Follow LSP specification links and examples

This architecture ensures type safety, high performance, and good extensibility while maintaining full compatibility with the LSP protocol.
