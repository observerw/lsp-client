# LSP-Client

A **full-featured, well-typed, and easy-to-use** Python LSP client library that provides a high-level interface to interact with Language Server Protocol servers.

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## 🚀 Quick Start

### Installation

```bash
uv add lsp-client
```

### Basic Usage

```python
from pathlib import Path
from lsp_client import Position
from lsp_client.clients.based_pyright import BasedPyrightClient

async def main():
    async with BasedPyrightClient(workspace="/path/to/my/project") as client:
        # Find references
        refs = await client.request_references(
            file_path="main.py",
            position=Position(line=10, character=5)
        )

        if not refs:
            print("No references found")
            return

        for ref in refs:
            print(f"Found reference: {ref.uri} at {ref.range}") 

        # Get document symbols
        symbols = await client.request_document_symbols("main.py")
```

## 📁 Project Structure

```
src/lsp_client/
├── client/           # Client base classes and utilities
├── server/           # Server base classes and process management
├── capability/       # LSP capability groups and protocols
├── clients/          # Server-specific client implementations
└── utils/            # Shared utilities
```

## 🤝 Contributing

Contributions are welcome! Please check the [contribution guide](CONTRIBUTING.md) for more information.

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🔗 Related Links

- [Language Server Protocol Specification](https://microsoft.github.io/language-server-protocol/)
- [lsprotocol](https://github.com/microsoft/lsprotocol) - LSP type definitions

---

**Making LSP integration simple and powerful!** 🚀
