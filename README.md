# LSP Client

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-pdoc-blue)](https://observerw.github.io/lsp-client/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/observerw/lsp-client)

A production-ready, async-first Python client for the Language Server Protocol (LSP). Built for developers who need fine-grained control, container isolation, and extensibility when integrating language intelligence into their tools.

## Why lsp-client?

`lsp-client` is engineered for developers building **production-grade tooling** that requires precise control over language server environments:

- **🐳 Container-First Architecture**: Containers as first-class citizens with workspace mounting, path translation, and lifecycle management. Pre-built images available, seamless switching between local and container environments.
- **🧩 Intelligent Capability Management**: Zero-overhead mixin system with automatic registration, negotiation, and availability checks. Only access methods for registered capabilities.
- **🎯 Complete LSP 3.17 Support**: Full specification implementation with pre-configured clients for Pyright, Rust-Analyzer, Deno, TypeScript, and Pyrefly.
- **⚡ Production-Ready & Modern**: Explicit environment control with no auto-downloads. Built with async patterns, comprehensive error handling, retries, and full type safety.

## Quick Start

### Installation

```bash
# Recommended: Use uv for modern Python dependency management
uv add lsp-client

# Or with pip
pip install lsp-client
```

### Local Language Server

The following code snippet can be run as-is, try it out:

```python
# install pyrefly with `uv tool install pyrefly` first
import anyio
from lsp_client import Position
from lsp_client.clients.pyrefly import PyreflyClient

async def main():
    async with PyreflyClient() as client:
        refs = await client.request_references(
            file_path="example.py",
            position=Position(10, 5)
        )
        for ref in refs:
            print(f"Reference at {ref.uri}: {ref.range}")

anyio.run(main)
```

### Container-based Language Server

```python
async def main():
    workspace = Path.cwd()
    async with PyrightClient(
        server=PyrightContainerServer(mounts=[workspace]),
        workspace=workspace
    ) as client:
        # Find definition of a symbol
        definitions = await client.request_definition_locations(
            file_path="example.py",
            position=Position(10, 5)
        )
        for def_loc in definitions:
            print(f"Definition at {def_loc.uri}: {def_loc.range}")

anyio.run(main)
```

### More Examples

The `examples/` directory contains comprehensive usage examples:

- `pyright_docker.py` - Using Pyright in Docker for Python analysis
- `rust_analyzer.py` - Rust code intelligence with Rust-Analyzer
- `pyrefly.py` - Python linting and analysis with Pyrefly
- `protocol.py` - Direct LSP protocol usage

Run examples with:

```bash
uv run examples/pyright_docker.py
```

## Supported Language Servers

| Language Server            | Module Path                        | Language              | Container Image                              |
| -------------------------- | ---------------------------------- | --------------------- | -------------------------------------------- |
| Pyright                    | `lsp_client.clients.pyright`       | Python                | `ghcr.io/observerw/lsp-client/pyright`       |
| Pyrefly                    | `lsp_client.clients.pyrefly`       | Python                | `ghcr.io/observerw/lsp-client/pyrefly`       |
| Rust Analyzer              | `lsp_client.clients.rust_analyzer` | Rust                  | `ghcr.io/observerw/lsp-client/rust-analyzer` |
| Deno                       | `lsp_client.clients.deno`          | TypeScript/JavaScript | `ghcr.io/observerw/lsp-client/deno`          |
| TypeScript Language Server | `lsp_client.clients.typescript`    | TypeScript/JavaScript | `ghcr.io/observerw/lsp-client/typescript`    |

Container images are automatically updated weekly to ensure access to the latest language server versions.

### Key Benefits

1. **Method Safety**: You can only call methods for capabilities you've registered. No runtime surprises from unavailable capabilities.
2. **Automatic Registration**: The mixin system automatically handles client registration, capability negotiation, and availability checks behind the scenes.
3. **Zero Boilerplate**: No manual capability checking, no complex initialization logic, no error handling for missing capabilities.
4. **Type Safety**: Full type annotations ensure you get compile-time guarantees about available methods.
5. **Composability**: Mix and match exactly the capabilities you need, creating perfectly tailored clients.

## Contributing

**We need your help!** 🙌 This project aims to support every major language server, each requiring detailed integration work with upstream projects. Whether you're an expert in Rust, Go, Java, or any other language, your contribution makes a real difference.

### How You Can Contribute

- **🚀 Add new language servers** - Know a language server that should be supported? [Add it!](docs/contribution/how-to-add-new-servers.md)
- **🧩 Implement LSP capabilities** - Help us support more of the LSP 3.17 spec. [Guide here](docs/contribution/how-to-add-new-capabilities.md)
- **🐳 Improve containers** - Optimize images, update versions, enhance cross-platform support
- **📚 Write docs & examples** - Tutorials, use cases, translations
- **🐛 Report bugs & test** - Share your experiences and edge cases

Every contribution—from fixing typos to implementing complex capabilities—helps the entire Python community. Read our [**Contributing Guide**](CONTRIBUTING.md) to get started!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on the [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) specification
- Uses [lsprotocol](https://github.com/microsoft/lsprotocol) for LSP type definitions
- Architecture inspired by [multilspy](https://github.com/microsoft/multilspy) and other LSP clients
