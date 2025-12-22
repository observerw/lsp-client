# Contributing to lsp-client-js

We welcome contributions to the TypeScript implementation of the LSP client!

## Development Workflow

### 1. Setup

Ensure you have [Bun](https://bun.sh) installed. Then install dependencies:

```bash
bun install
```

### 2. Coding Standards

We use **Biome** for linting and formatting. Please ensure your code passes the linting checks before submitting a PR.

```bash
# Check linting
bun run lint

# Auto-fix issues and format
bun run lint:fix
bun run format
```

### 3. Testing

Run the tests using Bun:

```bash
bun test
```

### 4. Examples

Test your changes by running the provided examples:

```bash
bun run examples/basic.ts
bun run examples/diagnostics.ts
```

## Project Structure

- `src/`: Core client implementation and capabilities.
- `examples/`: Usage examples for various language servers.
- `.biome.json`: Biome configuration.
