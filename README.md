# LSP Client

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/observerw/lsp-client)

A full-featured, well-typed, and easy-to-use Python client for the Language Server Protocol (LSP). This library provides a clean, async-first interface for interacting with language servers, supporting both local and Docker-based runtimes.

## Features

- **🚀 Async-first Design**: Built for high-performance concurrent operations
- **🔧 Full LSP Support**: Comprehensive implementation of LSP 3.17 specification
- **🐳 Docker Support**: Run language servers in isolated containers
- **📝 Type Safety**: Full type annotations with Pydantic validation
- **🧩 Modular Architecture**: Mixin-based capability system for easy extension
- **🎯 Production Ready**: Robust error handling with tenacity retries
- **📚 Well Documented**: Extensive documentation and examples

## Quick Start

### Installation

```bash
uv add lsp-client
```

### Basic Usage

```python
from pathlib import Path
import anyio
from lsp_client import Position
from lsp_client.clients.pyright import PyrightClient, PyrightLocalServer

async def main():
    workspace = Path.cwd()
    async with PyrightClient(
        workspace=workspace,
        server=PyrightLocalServer(),
    ) as client:
        # Find definition of something at line 11, character 28 in a file
        refs = await client.request_definition_locations(
            file_path="src/main.py",
            position=Position(11, 28)  # line 12, character 29 (1-indexed)
        )

        if not refs:
            print("No definition found.")
            return

        for ref in refs:
            print(f"Found definition at: {ref.uri} - Range: {ref.range}")

if __name__ == "__main__":
    anyio.run(main)
```

### Docker-based Language Server

```python
from pathlib import Path
import anyio
from lsp_client import Position
from lsp_client.clients.pyright import PyrightClient, PyrightDockerServer

async def main():
    workspace = Path.cwd()
    async with PyrightClient(
        workspace=workspace,
        server=PyrightDockerServer(mounts=[workspace]),
    ) as client:
        # Find definition of something at line 11, character 28 in a file
        refs = await client.request_definition_locations(
            file_path="src/main.py",
            position=Position(11, 28)
        )

        if not refs:
            print("No definition found.")
            return

        for ref in refs:
            print(f"Found definition at: {ref.uri} - Range: {ref.range}")

if __name__ == "__main__":
    anyio.run(main)
```

## Supported Language Servers

The library includes pre-configured clients for popular language servers:

| Language Server              | Module Path                          | Language              |
| ---------------------------- | ------------------------------------ | --------------------- |
| Pyright                      | `lsp_client.clients.pyright`         | Python                |
| Pyrefly                      | `lsp_client.clients.pyrefly`         | Python                |
| Rust Analyzer                | `lsp_client.clients.rust_analyzer`   | Rust                  |
| Deno                         | `lsp_client.clients.deno`            | TypeScript/JavaScript |
| TypeScript Language Server   | `lsp_client.clients.typescript`      | TypeScript/JavaScript |

## Contributing

We welcome contributions! Please see our [Contributing Guide](docs/contribution/) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on the [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) specification
- Uses [lsprotocol](https://github.com/microsoft/lsprotocol) for LSP type definitions
- Inspired by [multilspy](https://github.com/microsoft/multilspy) and other LSP clients
