# How to Add Support for a New LSP Server

**Why this matters**: Language servers are the core of this project. Each new server you add enables Python developers to leverage that language's intelligence—from autocomplete to refactoring—in their tools and workflows. The community needs contributors who understand specific language servers and can help integrate them properly.

This guide shows you how to add complete support for a new LSP server, including both the Python client and containerized deployment.

## Overview

Adding a new language server involves three main steps:

1. **Implement the Python client** - Create a client class with appropriate capability mixins
2. **Register for automatic versioning** - Enable automated updates from upstream
3. **Create a container image** - Package the server for isolated, reproducible environments

Let's walk through each step:

## 1. Implement the Client

Create a new file in `src/lsp_client/clients/` (e.g., `your_server.py`) and implement your client class by inheriting from `LSPClient` and relevant capability mixins.

Refer to existing implementations like `pyright.py` or `rust_analyzer.py` for inspiration.

Don't forget to export your new client in `src/lsp_client/clients/__init__.py`.

## 2. Register for Automatic Versioning

Add your server configuration to `registry/wiki.toml`. This allows the automation script to track the latest versions and update both the CI workflow and Docker build arguments.

Example entry:
```toml
[your-server]
type = "npm" # or "pypi", "github"
package = "your-server-package-name"
```

The system will automatically:
- Fetch the latest version from the provider.
- Update the GitHub Actions matrix.
- Update the `ARG VERSION` in your `ContainerFile`.

## 3. Create a Docker Environment

Create a directory for your server in `container/` and add a `ContainerFile`.

```bash
mkdir -p container/your-server
touch container/your-server/ContainerFile
```

Use multi-stage builds to keep the image size minimal. Ensure you use `ARG VERSION` for the server version.

Example `ContainerFile`:
```dockerfile
ARG VERSION=0.0.1
FROM node:22-slim AS builder
ARG VERSION
RUN npm install -g your-server-package-name@${VERSION}

FROM node:22-slim
COPY --from=builder /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=builder /usr/local/bin/your-server-binary /usr/local/bin/your-server-binary

WORKDIR /workspace
ENTRYPOINT ["your-server-binary", "--stdio"]
```

## 4. Verify

1. Run the version update script locally:
   ```bash
   python3 scripts/update_lsp_versions.py
   ```
2. Check if `.github/workflows/lsp-servers.yml` and your `ContainerFile` are updated with the latest version.
3. Commit and push your changes. The GitHub Action will build and push the new image to GHCR.

---

## Your Contribution Expands the Ecosystem

Adding support for a new language server is one of the most impactful contributions you can make:

- **Brings language intelligence to Python developers** working in that language
- **Reduces integration friction** for tools that need multi-language support
- **Demonstrates real-world usage patterns** that inform future improvements

The lsp-client project aims to be the go-to solution for LSP integration in Python, and that's only possible with community contributions covering diverse language ecosystems.

**Questions about a specific language server?** Feel free to open an issue or discussion—we're happy to help you navigate the integration process!

Thank you for helping make lsp-client better! 🚀
