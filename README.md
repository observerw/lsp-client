# LSP Client

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/observerw/lsp-client)

A full-featured, well-typed, and easy-to-use Python client for the Language Server Protocol (LSP). This library provides a clean, async-first interface for interacting with language servers, supporting both local and Docker-based runtimes.

## Why lsp-client?

`lsp-client` is designed specifically for developers who need **high control**, **isolation**, and **extensibility**:

- **🐳 Native Docker Support**: Unlike other clients that focus on local process management, `lsp-client` treats Docker as a first-class citizen. It handles the "magic" of mounting workspaces, translating file paths between your host and the container, and managing container lifecycles.
- **🧩 SDK for Custom Tooling**: Instead of being a closed wrapper, this is a true SDK. Our **Modular Capability System** allows you to build custom clients by mixing and matching only the LSP features you need, or even adding your own protocol extensions seamlessly.
- **🛠️ Explicit over Implicit**: We prioritize predictable environments. While other tools might auto-download binaries, `lsp-client` gives you full control over your server environment (Local or Docker), making it ideal for production-grade tools where version pinning is critical.
- **⚡ Modern Async-First Architecture**: Built from the ground up for Python 3.12+, utilizing advanced async patterns to ensure high-performance concurrent operations without blocking your main event loop.

## Features

- **🚀 Environment Agnostic**: Seamlessly switch between local processes and isolated Docker containers.
- **🔧 Full LSP 3.17 Support**: Comprehensive implementation of the latest protocol specification.
- **🎯 Specialized Clients**: Out-of-the-box support for popular servers (Pyright, Deno, Rust-Analyzer, etc.).
- **📝 Zero-Config Capabilities**: Automatically manages complex protocol handshakes and feature negotiations.
- **🧩 Pluggable & Modular**: Easily extend functionality or add support for custom LSP extensions.
- **🔒 Production-Grade Reliability**: Robust error handling, automatic retries, and full type safety.

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

| Language Server            | Module Path                        | Language              |
| -------------------------- | ---------------------------------- | --------------------- |
| Pyright                    | `lsp_client.clients.pyright`       | Python                |
| Pyrefly                    | `lsp_client.clients.pyrefly`       | Python                |
| Rust Analyzer              | `lsp_client.clients.rust_analyzer` | Rust                  |
| Deno                       | `lsp_client.clients.deno`          | TypeScript/JavaScript |
| TypeScript Language Server | `lsp_client.clients.typescript`    | TypeScript/JavaScript |

## Contributing

We welcome contributions! Please see our [Contributing Guide](docs/contribution/) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on the [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) specification
- Uses [lsprotocol](https://github.com/microsoft/lsprotocol) for LSP type definitions
- Inspired by [multilspy](https://github.com/microsoft/multilspy) and other LSP clients
