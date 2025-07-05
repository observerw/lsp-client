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

4. **Run tests to ensure everything works**:

   ```bash
   uv run pytest
   ```

## 📋 TODO List

## 🔧 Project Structure

```
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
