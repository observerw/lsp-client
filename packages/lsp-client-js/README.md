# lsp-client-js

A lightweight LSP (Language Server Protocol) client implementation in TypeScript using Bun.

## Features

- **Decentralized Capabilities**: Uses a feature-based architecture (inspired by the Python version's Mixins) to manage LSP capabilities independently.
- **Robust JSON-RPC**: Leverages `vscode-jsonrpc` for reliable communication with language servers.
- **Bun Optimized**: Built with Bun for high performance and modern TypeScript support.
- **Async Iterators**: Uses async generators for managing the client lifecycle.

## Architecture

The project follows the design principles outlined in `docs/DESIGN.md`:

1.  **Feature Registry**: Instead of Python's MRO, we use an explicit registration pattern for features (capabilities).
2.  **JSON-RPC Layer**: Built on top of `vscode-jsonrpc` which provides robust request/response matching and stream handling.
3.  **Lifecycle Management**: Async generators ensure proper initialization and cleanup (shutdown/exit/kill).

## Development

To run the examples:

```bash
# Basic hover example
bun run examples/basic.ts

# Diagnostics example
bun run examples/diagnostics.ts

# Pyrefly specific examples
bun run examples/pyrefly.ts
bun run examples/pyrefly_diagnostics.ts

# TypeScript `using` syntax examples
bun run examples/using_syntax.ts
bun run examples/using_advanced.ts
bun run examples/using_async.ts

# Rust-analyzer example
bun run examples/rust-analyzer.ts
```

## TypeScript `using` Syntax Integration

This project showcases TypeScript 5.2+'s **Explicit Resource Management** feature:

### Key Features Implemented

1. **Automatic Resource Cleanup**: LSP server connections are automatically disposed
2. **Exception Safety**: Resources are cleaned up even when errors occur
3. **Clean Syntax**: Eliminates manual `try/finally` blocks for resource management
4. **Stack-Based Order**: Disposal happens in correct LIFO order

### Usage Examples

#### Basic Resource Management
```typescript
{
  using server = new SafeLSPServer(['pyrefly', 'lsp']);
  const connection = await server.start();
  // Connection automatically disposed when scope ends
}
```

#### Error Safety
```typescript
try {
  using server = new SafeLSPServer(['pyrefly', 'lsp']);
  await server.start();
  throw new Error('Something went wrong');
} catch (e) {
  // Server is automatically disposed even with errors
}
```

#### Async Resource Management
```typescript
await using connection = await server.start();
// Async resources are automatically disposed
```

#### LSP Client Integration
```typescript
for await (const client of lspClient.start()) {
  // Client lifecycle automatically managed
  // Server disposed when generator exits
}
```

### Implementation Details

The project provides:
- **`SafeLSPServer`**: Implements `Disposable` for `using` compatibility
- **Enhanced LSPClient**: Uses `using` for automatic connection disposal
- **Resource Safety**: Ensures servers are killed and connections disposed

## Testing with Pyrefly

The project includes comprehensive tests with Pyrefly LSP server. To run the tests:

1. Ensure Pyrefly is installed: `pip install pyrefly` or `uv tool install pyrefly`
2. Create a `pyproject.toml` file in your project root with Pyrefly configuration
3. Run the Pyrefly examples to test hover, definition, and diagnostics features
