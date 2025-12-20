# How to Add Support for a New LSP Server

To add a new LSP server to this project, follow these steps to ensure both client support and containerized deployment are correctly configured.

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
