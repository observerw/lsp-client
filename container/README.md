# Container Registry

This directory contains Docker container configurations for LSP servers and a registry system for managing server versions.

## Directory Structure

```
container/
├── registry.toml           # Server registry configuration
├── registry.schema.json    # JSON schema for registry validation
└── <server-name>/          # Individual server configurations
    └── ContainerFile       # Docker container build instructions
```

## Adding a New LSP Server

To add a new LSP server, you need to:

1. Create a directory for the server
2. Create a `ContainerFile` with build instructions
3. Register the server in `registry.toml`

### Step 1: Create Server Directory and ContainerFile

Create a new directory with the server name and add a `ContainerFile`:

```dockerfile
# Example ContainerFile for a Node.js based LSP server
ARG VERSION=1.0.0
FROM docker.io/library/node:22-slim AS builder
ARG VERSION
RUN npm install -g <package-name>@${VERSION}

FROM docker.io/library/node:22-slim
ARG VERSION
LABEL org.opencontainers.image.version="${VERSION}"
COPY --from=builder /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=builder /usr/local/bin/<binary-name> /usr/local/bin/<binary-name>

WORKDIR /workspace
ENTRYPOINT ["<binary-name>", "--stdio"]
```

**Key points:**
- Use multi-stage builds to minimize final image size
- Define `ARG VERSION` for version management
- Set appropriate labels for metadata
- Use `--stdio` for LSP protocol communication
- Ensure the ENTRYPOINT runs the language server

### Step 2: Register in Registry

Add an entry to `registry.toml`:

```toml
[server-name]
type = "npm"        # or "pypi", "github", "custom"
package = "package-name"  # for npm/pypi
repo = "owner/repo"       # for github
strip_v = true      # optional, remove 'v' prefix from github releases
```

#### Registry Types

**npm**: For Node.js packages
```toml
[typescript]
type = "npm"
package = "typescript-language-server"
```

**pypi**: For Python packages
```toml
[pyrefly]
type = "pypi"
package = "pyrefly"
```

**github**: For GitHub releases
```toml
[rust-analyzer]
type = "github"
repo = "rust-lang/rust-analyzer"

[deno]
type = "github"
repo = "denoland/deno"
strip_v = true  # Remove 'v' prefix from version tags
```

**custom**: For custom version checking commands
```toml
[custom-server]
type = "custom"
command = "curl -s https://api.example.com/version | jq -r .version"
```

### Step 3: Build and Test

The CI system will automatically:
1. Check for new versions using the registry configuration
2. Build containers when versions change
3. Push images to the registry

To manually test:
```bash
# Build container (works with both Docker and Podman)
# Podman will automatically pick up 'ContainerFile'
docker build -f container/<server-name>/ContainerFile -t lsp/<server-name>:latest .
# or
podman build -t lsp/<server-name>:latest container/<server-name>/

# Test the container
docker run --rm lsp/<server-name>:latest --version
```

## Version Management

Versions are automatically updated via the `update_containers.yml` GitHub workflow:

1. `scripts/server_versions.py` reads `registry.toml` and fetches latest versions
2. Updates `ContainerFile` ARG VERSION values
3. Builds and pushes new container images
4. Commits version updates back to the repository

The workflow runs weekly or can be triggered manually with the "force" option.