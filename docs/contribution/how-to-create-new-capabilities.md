# How to Add a New LSP Capability

This guide details the process for adding new Language Server Protocol (LSP) capabilities to this library. Familiarity with the [LSP 3.17 specification](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/) and the library's Protocol/Mixin design pattern is recommended.

## Design Philosophy

The library's architecture is based on composable mixins, where each LSP capability is a self-contained unit.

- **Capabilities as Mixins**: Each capability is a `Protocol` named `WithRequestX`, `WithNotifyX`, `WithReceiveX`, or `WithRespondX`.
- **Categorization**: Capabilities are grouped by LSP category (e.g., `textDocument`, `workspace`). Base protocols like `TextDocumentCapabilityProtocol` enforce this structure. All capabilities inherit from `CapabilityClientProtocol` to access core client methods (`request`, `notify`, `file_request`).
- **Auto-registration and Validation**: On initialization, `LSPClient` discovers all mixin capabilities, registers them, and verifies server support via `assert` ("let it crash" principle).
- **Server Hooks**: For capabilities where the server initiates communication (notifications or requests), the capability must implement `ServerRequestHookProtocol` and register itself in `register_server_request_hooks`.
- **Capability Operations**:
  - **Client Requests**: Use `request(...)` to send requests that expect a response.
  - **Client Notifications**: Use `notify(...)` for notifications that do not expect a response.
  - **File-based Requests**: Use `file_request(...)` for requests that require files to be opened/synchronized before execution.
  - **Server Notifications**: Implement a `receive_*` method and register a `ServerNotificationHook`.
  - **Server Requests**: Implement a `respond_*` method and register a `ServerRequestHook`.

Examples:

- Request: reference implementation exists in `request` subpackage (e.g., `definition.py`)
- Notification: reference implementation exists in `notification` subpackage (e.g., `text_document_synchronize.py`)
- Server-side: reference implementation exists in `server_notification` and `server_request` subpackages

## Steps to Add a Capability

**1. Identify LSP Method and Category**
Consult the LSP 3.17 specification for the method string (e.g., `textDocument/definition`) and its category. Use constants from `lsp_type` (e.g., `lsp_type.TEXT_DOCUMENT_DEFINITION`).

**2. Create Capability Module**
Create a new module in the corresponding subpackage:

- Client Requests: under `src/lsp_client/capability/request/`
- Client Notifications: under `src/lsp_client/capability/notification/`
- Server Notifications: under `src/lsp_client/capability/server_notification/`
- Server Requests: under `src/lsp_client/capability/server_request/`

**3. Implement Capability Protocol (Mixin)**
The capability class must:

- Inherit from the appropriate category protocol (e.g., `TextDocumentCapabilityProtocol`) and `CapabilityClientProtocol`.
- For server-initiated messages, also inherit from `ServerRequestHookProtocol`.
- Implement these class methods:
  - `methods()`: Return a tuple of LSP method strings (use `lsp_type` constants).
  - Category-specific registration method to declare client support:
    - `register_text_document_capability(...)`
    - `register_workspace_capability(...)`
    - `register_window_capability(...)`
    - `register_notebook_document_capability(...)`
    - `register_general_capability(...)`
  - `check_server_capability(...)`: Assert server support. Always call `super().check_server_capability(cap)`.
- For server messages, implement `register_server_request_hooks(self, registry: ServerRequestHookRegistry)`.
- Implement the method for the capability's action (`request_*`, `notify_*`, `receive_*`, `respond_*`).

**4. Export Capability**
Add the new capability to the `__all__` list in the package's `__init__.py`.

**5. Integrate into Client**
Add the new mixin to your client class's inheritance list. `LSPClient` handles automatic setup.

**6. Validate**
Test the implementation by making a request or sending a notification. Verify logs and return values.

## Code Templates

### Request Capability with a Single Return Type

```python
from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.utils.types import AnyPath, Position, lsp_type

from lsp_client.protocol import CapabilityClientProtocol, TextDocumentCapabilityProtocol


@runtime_checkable
class WithRequestX(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/x` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_x
    """

    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (lsp_type.TEXT_DOCUMENT_X,)

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        # Declare client support per spec
        cap.x = lsp_type.XClientCapabilities(...)

    @override
    @classmethod
    def check_server_capability(
        cls,
        cap: lsp_type.ServerCapabilities
    ) -> None:
        super().check_server_capability(cap)
        assert cap.x_provider

    async def request_x(
        self, file_path: AnyPath, position: Position
    ) -> lsp_type.XResponse | None:
        return await self.file_request(
            lsp_type.XRequest(
                id=jsonrpc_uuid(),
                params=lsp_type.XParams(
                    text_document=lsp_type.TextDocumentIdentifier(uri=self.as_uri(file_path)),
                    position=position,
                ),
            ),
            schema=lsp_type.XResponse,
            file_paths=[file_path],  # Ensures didOpen/didClose is handled
        )
```

### Workspace Request Template

For requests that do not require document context, use `self.request` directly.

```python
@runtime_checkable
class WithRequestWorkspaceX(
    WorkspaceCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (lsp_type.WORKSPACE_X,)

    @override
    @classmethod
    def check_server_capability(
        cls,
        cap: lsp_type.ServerCapabilities
    ) -> None:
        super().check_server_capability(cap)
        assert cap.workspace_x_provider

    async def request_workspace_x(self, query: str) -> lsp_type.WorkspaceXResponse | None:
        return await self.request(
            lsp_type.WorkspaceXRequest(
                id=jsonrpc_uuid(),
                params=lsp_type.WorkspaceXParams(query=query),
            ),
            schema=lsp_type.WorkspaceXResponse,
        )
```

### Client Notification Template

```python
from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

from lsp_client.utils.types import AnyPath, lsp_type

from lsp_client.protocol import CapabilityClientProtocol, TextDocumentCapabilityProtocol


@runtime_checkable
class WithNotifyX(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/x` - e.g., didOpen/didChange/didClose
    """

    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (lsp_type.TEXT_DOCUMENT_X,)

    @override
    @classmethod
    def register_text_document_capability(cls, cap: lsp_type.TextDocumentClientCapabilities) -> None:
        cap.synchronization = lsp_type.TextDocumentSyncClientCapabilities(...)

    @override
    @classmethod
    def check_server_capability(
        cls,
        cap: lsp_type.ServerCapabilities
    ) -> None:
        super().check_server_capability(cap)
        assert cap.text_document_sync

    async def notify_x(self, file_path: AnyPath) -> None:
        await self.notify(
            msg=lsp_type.DidXTextDocumentNotification(
                params=lsp_type.DidXTextDocumentParams(
                    text_document=lsp_type.TextDocumentIdentifier(uri=self.as_uri(file_path)),
                )
            )
        )
```

### Server-Sent Notification Template

```python
from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

from lsp_client.protocol import (
    CapabilityClientProtocol,
    ServerNotificationHook,
    ServerRequestHookProtocol,
    ServerRequestHookRegistry,
    TextDocumentCapabilityProtocol,
)
from lsp_client.utils.types import lsp_type


@runtime_checkable
class WithReceiveX(
    TextDocumentCapabilityProtocol,
    ServerRequestHookProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/x` notification from server
    """

    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (lsp_type.TEXT_DOCUMENT_X,)

    @override
    @classmethod
    def check_server_capability(
        cls,
        cap: lsp_type.ServerCapabilities
    ) -> None:
        super().check_server_capability(cap)

    async def receive_x(self, noti: lsp_type.XNotification) -> None:
        # Handle server notification
        pass

    @override
    def register_server_request_hooks(
        self, registry: ServerRequestHookRegistry
    ) -> None:
        super().register_server_request_hooks(registry)
        registry.register(
            lsp_type.TEXT_DOCUMENT_X,
            ServerNotificationHook(
                cls=lsp_type.XNotification,
                execute=self.receive_x,
            ),
        )
```

### Server Request Template

```python
from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

from lsp_client.protocol import (
    CapabilityClientProtocol,
    ServerRequestHook,
    ServerRequestHookProtocol,
    ServerRequestHookRegistry,
    WorkspaceCapabilityProtocol,
)
from lsp_client.utils.types import lsp_type


@runtime_checkable
class WithRespondX(
    WorkspaceCapabilityProtocol,
    ServerRequestHookProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `workspace/x` request from server
    """

    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (lsp_type.WORKSPACE_X,)

    @override
    @classmethod
    def check_server_capability(
        cls,
        cap: lsp_type.ServerCapabilities
    ) -> None:
        super().check_server_capability(cap)

    async def respond_x(self, req: lsp_type.XRequest) -> lsp_type.XResponse:
        # Return response object
        return lsp_type.XResponse(id=req.id, result=...)

    @override
    def register_server_request_hooks(
        self, registry: ServerRequestHookRegistry
    ) -> None:
        super().register_server_request_hooks(registry)
        registry.register(
            lsp_type.WORKSPACE_X,
            ServerRequestHook(
                cls=lsp_type.XRequest,
                execute=self.respond_x,
            ),
        )
```

## Conventions

- **Module Locations**: place capability modules under `request`, `notification`, `server_notification`, or `server_request` subpackages.
- **Class Names**:
  - Client Request: `WithRequest<Feature>`
  - Client Notification: `WithNotify<Feature>`
  - Server Notification: `WithReceive<Feature>`
  - Server Request: `WithRespond<Feature>`
- **Method Names**:
  - `request_<feature>`, `notify_<feature>`, `receive_<feature>`, `respond_<feature>`
- **Required Implementations**:
  - `methods()` (use `lsp_type` constants)
  - Category-specific `register_*_capability(...)`
  - `check_server_capability(...)` (always call `super()`)
  - `register_server_request_hooks(...)` (for server messages)
- **Exports**: Add new classes to `__init__.py`'s `__all__` list.

## Client Integration

Add the capability as a mixin to your client class:

```python
@define
class MyClient(
    LSPClient[MyServer],
    WithRequestDefinition,  # ... add new mixin here
):
    ...
```

`LSPClient` handles capability registration and validation automatically during initialization. When making requests that require document context, use `file_request` to ensure `didOpen`/`didClose` notifications are handled.

## Common Pitfalls

- **Missing `super()` Call**: Forgetting to call `super().check_server_capability()` or `super().register_server_request_hooks(...)` can break the inheritance chain.
- **Missing Export**: An `ImportError` may indicate the capability was not added to `__init__.py`.
- **Missing `file_paths`**: Failure to use `file_request` or manually handle synchronization prevents the server from seeing the document content.
- **Assertion Failure**: An `assert` failure on startup indicates the server does not support the capability.
- **Response Type Guards**: For `Union` return types, use type guards like `is_locations` to handle responses safely.
