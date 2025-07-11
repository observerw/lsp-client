# Contributing to LSP Client

Thank you for your interest in contributing to LSP Client! This guide will help you get started with contributing to this project.

## 🚀 Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) for dependency management
- Git

### Setting Up Development Environment

1. **Fork and clone the repository**:

   ```bash
   git clone https://github.com/your-username/lsp-client.git
   cd lsp-client
   ```

2. **Install dependencies**:

   ```bash
   uv sync --dev
   ```

3. **Activate the virtual environment**:

   ```bash
   source .venv/bin/activate
   ```

## 📋 TODO List

- [ ] Add more documentation
- [ ] Support more LSP capabilities
- [ ] Add more tests for existing capabilities
- [ ] Add support for MCP
- [ ] Add support for [streamable-HTTP MCP](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports) support
- [ ] Add documentation on how to auto installation of LSP servers
- [ ] Add support for export result
- [ ] Add support for file watching & automatic DocumentSync capabilities
- [ ] Add support for static mode
- [ ] Add support for automatically generating client side capabilities from server capabilities

## 🔧 Project Structure

```text
src/lsp_client/
├── __init__.py           # Main exports
├── jsonrpc.py           # JSON-RPC implementation
├── types.py             # Type definitions
├── capability/          # LSP capability handling
├── client/              # Client-side implementations
├── server/              # Server management
├── servers/             # Specific LSP server implementations
└── utils/               # Utility functions
```

## 📚 Resources

- [Language Server Protocol Specification](https://microsoft.github.io/language-server-protocol/)

## 🤝 Getting Help

- Open an issue for questions or problems
- Check existing issues and discussions
- Read the documentation and examples
- Look at the test files for usage patterns

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.

---

Happy coding! 🎉
