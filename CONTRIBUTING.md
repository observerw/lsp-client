# Contributing to LSP Client

Thank you for your interest in contributing to lsp-client! 🎉

## Why Your Contribution Matters

This project is unique in its ambitious scope: **we aim to provide production-ready Python clients for every major language server**, each with its own intricate protocol details, configuration quirks, and containerization requirements.

**We need your help!** The LSP Client project interfaces with numerous upstream projects:

- **Language Servers**: Pyright, Rust-Analyzer, TypeScript, Deno, Pyrefly, and many more to come
- **LSP Protocol**: The ever-evolving LSP 3.17+ specification with 50+ capabilities
- **Container Ecosystems**: Docker/Podman images, version management, and build systems
- **Upstream Dependencies**: npm packages, PyPI distributions, GitHub releases

Each integration requires:
- Deep understanding of the specific language server's capabilities and behavior
- Careful testing across different environments (local, container, multi-workspace)
- Maintaining compatibility as upstream projects evolve
- Documenting edge cases and configuration options

**No single maintainer can keep up with all these moving parts.** Your expertise with specific language servers, protocols, or use cases is invaluable. Whether you use Rust, Python, TypeScript, or any other language, you have unique insights that can improve this project for everyone.

## How You Can Help

We welcome all kinds of contributions:

### 🚀 Add Support for New Language Servers

Know a language server that would benefit the community? We'd love to integrate it! See our detailed guide:

**→ [How to Add Support for a New LSP Server](docs/contribution/how-to-add-new-servers.md)**

Common servers we'd love to see:
- **Go**: gopls
- **Java**: Eclipse JDT, jdtls
- **C/C++**: clangd
- **Ruby**: Solargraph, Sorbet
- **PHP**: Intelephense
- **And many more!**

### 🧩 Implement LSP Capabilities

The LSP specification includes 50+ capabilities. We've implemented the most common ones, but there's much more to do:

**→ [How to Add a New LSP Capability](docs/contribution/how-to-add-new-capabilities.md)**

Capabilities we need:
- **textDocument/inlayHint** - inline type hints
- **textDocument/inlineValue** - debugger inline values
- **textDocument/colorPresentation** - color picker support
- **textDocument/linkedEditingRange** - rename refactoring
- **workspace/symbol** - project-wide symbol search
- And more from the [LSP 3.17 spec](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/)

### 🐳 Improve Container Support

Help us maintain and improve our container images:
- Update versions in `registry/wiki.toml`
- Optimize Dockerfiles for smaller image sizes
- Add new base images for different environments
- Improve cross-platform compatibility

### 📚 Documentation & Examples

- Write tutorials for specific use cases
- Add examples for your favorite language server
- Improve API documentation
- Translate documentation to other languages

### 🐛 Bug Reports & Testing

- Report issues with specific language servers
- Test edge cases in your environment
- Improve test coverage
- Share your integration experiences

### 💡 Feature Requests & Discussion

Have ideas for improving the API? Want to discuss architecture decisions? Open an issue or start a discussion!

## Getting Started

### Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/observerw/lsp-client.git
   cd lsp-client
   ```

2. **Install dependencies** (we recommend [uv](https://github.com/astral-sh/uv)):
   ```bash
   uv sync --all-extras
   ```

3. **Set up pre-commit hooks**:
   ```bash
   uv run pre-commit install
   ```

### Development Workflow

See [AGENTS.md](AGENTS.md) for detailed development commands:

```bash
# Lint & format
ruff check --fix && ruff format

# Type checking
mypy src/

# Run tests
pytest                    # All tests
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests
pytest path/to/test.py::test_function  # Single test
```

### Code Style

- **Python 3.12+** required
- Use `from __future__ import annotations` in all files
- Follow [PEP 8](https://peps.python.org/pep-0008/) (enforced by ruff)
- Full type annotations required (checked by mypy)
- Write clear docstrings for public APIs

### Commit Guidelines

- Write clear, descriptive commit messages
- Use conventional commits format:
  - `feat:` new features
  - `fix:` bug fixes
  - `docs:` documentation changes
  - `test:` test additions/changes
  - `refactor:` code refactoring
  - `chore:` maintenance tasks

Examples:
```
feat(lsp): add support for gopls language server
fix(container): resolve path translation issue in Windows
docs: add tutorial for rust-analyzer integration
test: add integration tests for multi-root workspaces
```

## Pull Request Process

1. **Fork the repository** and create a branch from `main`
2. **Make your changes** following the code style guidelines
3. **Add tests** for new functionality
4. **Update documentation** as needed
5. **Ensure all tests pass**: `pytest`
6. **Run linting**: `ruff check --fix && ruff format`
7. **Submit a pull request** with a clear description of your changes

### PR Checklist

- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Code follows style guidelines (ruff, mypy)
- [ ] Commit messages are clear and descriptive
- [ ] PR description explains the motivation and changes

## Need Help?

- **Questions?** Open a [Discussion](https://github.com/observerw/lsp-client/discussions)
- **Bug reports?** Open an [Issue](https://github.com/observerw/lsp-client/issues)
- **Want to chat?** Reach out in the Issues or Discussions

## Recognition

All contributors will be recognized in our release notes and documentation. We deeply appreciate every contribution, no matter how small!

---

**Remember**: Every language server you help integrate, every capability you implement, and every bug you fix makes this library better for the entire Python community. Your contribution has real impact! 🚀
