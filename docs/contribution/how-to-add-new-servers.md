# How to Add Support for a New LSP Server

This guide provides a Standard Operating Procedure (SOP) for contributors to add support for a new LSP server to `lsp-client`.

## Overview

Adding a new server involves two main parts:

1.  **Client Implementation**: Writing the Python class that interacts with the LSP server.
2.  **Infrastructure**: Setting up automatic versioning and containerization.

---

## Step 1: Client Implementation

### 1.1 Choose File Structure

- **Simple Server**: If the implementation is straightforward, create a single file: `src/lsp_client/clients/your_server.py`.
- **Complex Server**: If you need custom models or many extension methods, create a directory: `src/lsp_client/clients/your_server/` with `__init__.py`, `client.py`, `models.py`, and `extension.py`.

### 1.2 Define the Client Class

Your client must inherit from `LSPClient` and relevant capability mixins. Use the `@define` decorator from `attrs`.

```python
from __future__ import annotations
from typing import Any, override
from attrs import define
from lsp_client.client.abc import LSPClient
from lsp_client.server.abc import LSPServer
from lsp_client.server.local import LocalServer
from lsp_client.utils.types import lsp_type

# Import required capabilities
from lsp_client.capability.request import WithRequestHover, WithRequestDefinition
from lsp_client.capability.server_notification import WithReceivePublishDiagnostics

@define
class YourServerClient(
    LSPClient,
    WithRequestHover,
    WithRequestDefinition,
    WithReceivePublishDiagnostics,
    # Add other capabilities as needed
):
    """
    - Language: YourLanguage
    - Homepage: https://example.com
    - Github: https://github.com/example/your-server
    """

    # Add configuration options as fields
    enable_feature_x: bool = True

    @override
    def get_language_id(self) -> lsp_type.LanguageKind:
        return lsp_type.LanguageKind.YourLanguage  # Ensure this exists in LanguageKind

    @override
    def create_default_server(self) -> LSPServer:
        return LocalServer(command=["your-server-binary", "--stdio"])

    @override
    def create_initialization_options(self) -> dict[str, Any]:
        # Provide any initialization options required by the server
        return {
            "enableFeatureX": self.enable_feature_x,
        }

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        """Optional: Check if the server version/name is compatible."""
        return

    @override
    async def ensure_installed(self) -> None:
        """Implement logic to check and/or install the server binary."""
        import shutil
        if shutil.which("your-server-binary"):
            return
        # Optional: Add installation logic or raise RuntimeError
        raise RuntimeError("your-server-binary not found. Please install it.")
```

### 1.3 Capability Mixins

The client uses a mixin-based approach for LSP capabilities. You should only include what the server supports:

- **Requests (Client -> Server)**: `WithRequestHover`, `WithRequestDefinition`, `WithRequestReferences`, etc.
- **Notifications (Client -> Server)**: `WithNotifyDidChangeConfiguration`, `WithNotifyDidOpen`, etc.
- **Server Notifications (Server -> Client)**: `WithReceivePublishDiagnostics`, `WithReceiveLogMessage`, etc.
- **Server Requests (Server -> Client)**: `WithRespondConfigurationRequest`, `WithRespondWorkspaceFoldersRequest`, etc.

Refer to `src/lsp_client/capability/` for available mixins.

---

## Step 2: Custom Extensions (Optional)

If the server has non-standard LSP methods (e.g., Deno's `deno/cache`), follow these steps:

1.  Define models for requests/responses in `models.py` (or top of the file).
2.  Create a capability mixin in `extension.py` or the main file.
3.  Inherit from `CapabilityProtocol` and `CapabilityClientProtocol`.

```python
@runtime_checkable
class WithRequestCustomMethod(CapabilityProtocol, CapabilityClientProtocol, Protocol):
    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return ("custom/methodName",)

    async def request_custom_method(self, params: CustomParams) -> CustomResponse:
        return await self.request(
            CustomRequest(id=jsonrpc_uuid(), params=params),
            schema=CustomResponse
        )
```

---

## Step 3: Registration and Export

Export your client in `src/lsp_client/clients/__init__.py`.

```python
# src/lsp_client/clients/__init__.py
from .your_server import YourServerClient

# Export with a meaningful name if needed
YourServerLSPClient = YourServerClient

__all__ = [
    "YourServerLSPClient",
]
```

---

## Step 4: Infrastructure (Containerization & Versioning)

### 4.1 Register for Automatic Versioning

Add your server to `container/registry.toml`. This allows CI to automatically track the latest version.

```toml
[your-server]
type = "npm" # or "pypi", "github", "custom"
package = "your-server-package-name" # for npm/pypi
# repo = "owner/repo" # for github
# command = "curl -s https://api.example.com/version | jq -r .version" # for custom
```

### 4.2 Create a ContainerFile

Create `container/your-server/ContainerFile`. Use `ARG VERSION` to allow automated updates.

```dockerfile
ARG VERSION=latest
FROM node:22-slim AS builder
ARG VERSION
RUN npm install -g your-server-package-name@${VERSION}

FROM node:22-slim
COPY --from=builder /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=builder /usr/local/bin/your-server-binary /usr/local/bin/your-server-binary

WORKDIR /workspace
ENTRYPOINT ["your-server-binary", "--stdio"]
```

### 4.3 Define Container Server

In your client file, add a partial for the containerized server:

```python
from lsp_client.server.container import ContainerServer
from functools import partial

YourServerContainerServer = partial(
    ContainerServer, image="ghcr.io/observerw/lsp-client/your-server:latest"
)
```

---

## SOP Checklist

- [ ] Client class created with `@define`.
- [ ] Inherited from `LSPClient` and necessary `With...` capabilities.
- [ ] `get_language_id` implemented.
- [ ] `create_default_server` implemented.
- [ ] `create_initialization_options` implemented.
- [ ] `ensure_installed` implemented.
- [ ] Exported in `src/lsp_client/clients/__init__.py`.
- [ ] `container/registry.toml` entry added.
- [ ] `container/your-server/ContainerFile` created.
