# How to Add a New LSP Capability

**Why this matters**: The Language Server Protocol specification includes 50+ capabilities, from basic autocomplete to advanced refactoring. Each capability you implement opens up new possibilities for developers building intelligent tools. This project needs contributors familiar with different parts of the LSP spec to help achieve complete coverage.

This guide provides a comprehensive walkthrough for adding new LSP capabilities to the library. Whether you're implementing a common capability like `textDocument/inlayHint` or something more specialized, this guide will help you follow the project's architecture patterns.

## Prerequisites

Before starting, familiarize yourself with:
- The [LSP 3.17 specification](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/)
- The library's Protocol/Mixin design pattern (see examples in `src/lsp_client/capability/`)
- Python's `Protocol` and `runtime_checkable` decorators

## Design Philosophy

The library's architecture is based on composable mixins, where each LSP capability is a self-contained unit.

- **Capabilities as Mixins**: Each capability is a `Protocol` named `WithRequestX`, `WithNotifyX`, `WithReceiveX`, or `WithRespondX`.
- **Categorization**: Capabilities are grouped by LSP category (e.g., `textDocument`, `workspace`). Base protocols like `LSPTextDocumentCapabilityProtocol` enforce this structure. All capabilities inherit from `LSPCapabilityClientProtocol` to access core client methods (`_request`, `_notify`).
- **Auto-registration and Validation**: On initialization, `LSPClient` discovers all mixin capabilities, registers them, and verifies server support via `assert` ("let it crash" principle).
- **Capability Operations**:
  - **Client Requests**: Use `_request(...)` to send requests that expect a response.
  - **Client Notifications**: Use `_notify(...)` for notifications that do not expect a response.
  - **Server Notifications**: Implement a `receive_*` method to handle notifications from the server.
  - **Server Requests**: Implement a `respond_*` method to handle requests from the server.

Examples:

- Request: reference implementation exists in the request subpackage
- Notification: reference implementation exists in the notification subpackage

## Steps to Add a Capability

**1. Identify LSP Method and Category**
Consult the LSP 3.17 specification for the method string (e.g., `textDocument/definition`) and its category.

**2. Create Capability Module**
Create a new module in the corresponding subpackage:

- Requests: under the request subpackage
- Notifications: under the notification subpackage
- Server-side: under the response subpackage

**3. Implement Capability Protocol (Mixin)**
The capability class must:

- Inherit from the appropriate category protocol (e.g., `LSPTextDocumentCapabilityProtocol`) and `LSPCapabilityClientProtocol`.
- Implement three class methods:
  - `methods()`: Return a tuple of LSP method strings.
  - Category-specific registration method to declare client support:
    - `register_text_document_capability(...)`
    - `register_workspace_capability(...)`
    - `register_window_capability(...)`
    - `register_notebook_document_capability(...)`
    - `register_general_capability(...)`
  - `check_server_capability(...)`: Assert server support.
- Implement the method for the capability's action (`request_*`, `notify_*`, `receive_*`, `respond_*`).

**4. Export Capability**
Add the new capability to the `__all__` list in the package's `__init__.py`.

**5. Integrate into Client**
Add the new mixin to your client class's inheritance list. `LSPClient` handles automatic setup.

**6. Validate**
Test the implementation by making a request or sending a notification. Verify logs and return values. For server-initiated communication, ensure the server request dispatch logic is updated.

## Code Templates

### Request Capability with a Single Return Type

This template covers the most common use case, where a request returns a single, predictable type.

```python
from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

from lsp_client.utils.jsonrpc import jsonrpc_uuid
from lsp_client.utils.types import AnyPath, Position, lsp_type

from lsp_client.protocol import LSPCapabilityClientProtocol, LSPTextDocumentCapabilityProtocol


@runtime_checkable
class WithRequestX(
    LSPTextDocumentCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/x` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_x
    """

    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return ("textDocument/x",)

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        # Declare client support per spec; can be empty for simple capabilities
        pass

    @override
    @classmethod
    def check_server_capability(
        cls,
        cap: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ) -> None:
        assert cap.x_provider

    async def request_x(
        self, file_path: AnyPath, position: Position
    ) -> lsp_type.XResponse | None:
        return await self._request(
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

### Client Notification Template

```python
from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

from lsp_client.utils.types import AnyPath, lsp_type

from lsp_client.protocol import LSPCapabilityClientProtocol, LSPTextDocumentCapabilityProtocol


@runtime_checkable
class WithNotifyX(
    LSPTextDocumentCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/x` - e.g., didOpen/didChange/didClose
    """

    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return ("textDocument/x",)

    @override
    @classmethod
    def register_text_document_capability(cls, cap: lsp_type.TextDocumentClientCapabilities) -> None:
        cap.synchronization = lsp_type.TextDocumentSyncClientCapabilities(
            will_save=True,
            will_save_wait_until=True,
            did_save=True,
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        cap: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ) -> None:
        assert cap.text_document_sync

    async def notify_x(self, file_path: AnyPath) -> None:
        await self._notify(
            msg=lsp_type.DidXTextDocumentNotification(
                params=lsp_type.DidXTextDocumentParams(
                    text_document=lsp_type.TextDocumentIdentifier(uri=self.as_uri(file_path)),
                )
            )
        )
```

### Handling Complex Return Types and Work-Done Progress

Some LSP methods, like `textDocument/definition`, can return multiple types (e.g., `Location | Sequence[Location] | Sequence[LocationLink]`). In these cases, you can provide convenience wrappers to handle type ambiguity while preserving `None` to reflect server semantics. Use type guards to ensure runtime safety.

For long-running operations, you can also support work-done progress reporting. This is achieved by adding a `work_done_handlers` parameter and using the `create_work_done_progress` context manager to supply a `work_done_token` to the request.

```python
# (imports from the simple request example plus these)
from loguru import logger
from lsp_client.utils.type_guard import is_locations, is_location_links
from lsp_client.protocol import WorkDoneHandlers


# ... (class definition and methods are the same as the simple request)

    async def request_x(
        self,
        file_path: AnyPath,
        position: Position,
        *,
        work_done_handlers: WorkDoneHandlers | None = None,
    ) -> (
        lsp_type.Location | Sequence[lsp_type.Location] | Sequence[lsp_type.LocationLink] | None
    ):
        with self.create_work_done_progress(
            id := jsonrpc_uuid(),
            handlers=work_done_handlers,
        ) as work_done_token:
            return await self._request(
                lsp_type.XRequest(
                    id=id,
                    params=lsp_type.XParams(
                        text_document=lsp_type.TextDocumentIdentifier(
                            uri=self.as_uri(file_path)
                        ),
                        position=position,
                        work_done_token=work_done_token,
                    ),
                ),
                schema=lsp_type.XResponse,
                file_paths=[file_path],
            )

    # Convenience wrapper: return locations or None (preserve None)
    async def request_x_locations(
        self,
        file_path: AnyPath,
        position: Position,
        *,
        work_done_handlers: WorkDoneHandlers | None = None,
    ) -> Sequence[lsp_type.Location] | None:
        match await self.request_x(
            file_path,
            position,
            work_done_handlers=work_done_handlers,
        ):
            case lsp_type.Location() as loc:
                return [loc]
            case locations if is_locations(locations):
                return list(locations)
            case None:
                return None
            case other:
                logger.warning("X result returned with unexpected type: {}", other)
                return None

    # Convenience wrapper: return location links or None (preserve None)
    async def request_x_links(
        self,
        file_path: AnyPath,
        position: Position,
        *,
        work_done_handlers: WorkDoneHandlers | None = None,
    ) -> Sequence[lsp_type.LocationLink] | None:
        match await self.request_x(
            file_path,
            position,
            work_done_handlers=work_done_handlers,
        ):
            case links if is_location_links(links):
                return list(links)
            case None:
                return None
            case other:
                logger.warning("X result returned with unexpected type: {}", other)
                return None
```

### Preserving `None` Return Values

It is crucial to distinguish between a `None` response and an empty sequence (`[]`).

According to the Language Server Protocol specification, certain operations may return:

- An empty sequence (`[]`) to indicate that the operation was successful but yielded no results.
- A `None` (or `null`) value to signify that the operation is not supported by the server or that no meaningful result could be produced.

Given this distinction, both the base `request_*` method and any convenience wrappers **must** preserve the `None` response when the specification allows for it. Do not coalesce `None` into an empty sequence, to avoid masking unsupported operations or misrepresenting server outcomes.

### Server-Sent Notifications and Requests

- **Server Notifications**: Implement a `WithReceiveX` mixin with a `receive_x(req: ...) -> None` method.
- **Server Requests**: Implement a `WithRespondX` mixin with a `respond_x(req: ...) -> ResponseType` method.
- **Note**: Update the server request dispatch function to route the new capability.
  - **Naming**: Use `respond_*` for requests and `receive_*` for notifications.

## Conventions

- **Module Locations**: place capability modules under request, notification, or response subpackages
- **Class Names**:
  - Client Request: `WithRequest<Feature>`
  - Client Notification: `WithNotify<Feature>`
  - Server Notification: `WithReceive<Feature>`
  - Server Request: `WithRespond<Feature>`
- **Method Names**:
  - `request_<feature>`, `notify_<feature>`, `receive_<feature>`, `respond_<feature>`
- **Required Implementations**:
  - `methods()`
  - Category-specific `register_*_capability(...)`
  - `check_server_capability(...)`
- **Exports**: Add new classes to `__init__.py`'s `__all__` list.

## Client Integration

Add the capability as a mixin to your client class:

```python
@define
class PyreflyClient(
    LSPClient[PyreflyServer],
    WithRequestReferences,  # ... add new mixin here
):
    @property
    @override
    def language_id(self) -> lsp_type.LanguageKind:
        return lsp_type.LanguageKind.Python
```

`LSPClient` handles capability registration and validation (automatically calls category-specific `register_*_capability` and performs `check_server_capability` during initialization). When making requests, pass `file_paths=[...]` to trigger `didOpen`/`didClose` notifications.

Note: Server requests/notifications are dispatched by a dedicated function using pattern matching; add a corresponding branch when introducing new server-side capabilities.

## Common Pitfalls

- **Mismatched Routing Names**: For server-side capabilities, ensure `WithReceive*` / `WithRespond*` class and method names match the server request dispatch logic.
- **Missing Export**: An `ImportError` may indicate the capability was not added to `__init__.py`.
- **Missing `file_paths`**: Failure to pass `file_paths` in requests prevents `didOpen`/`didClose` synchronization.
- **Assertion Failure**: An `assert` failure on startup indicates the server does not support the capability.
- **Response Type Guards**: For `Union` return types, use type guards like `is_locations` to handle responses safely.

## Commit Guidelines

- Use small, atomic commits.
- Write clear and concise commit messages.
- **Example**: `feat(lsp): add textDocument/typeDefinition capability mixin`
- **Example**: `docs: add contribution guide for new capabilities`

### Workspace Request Template

```python
from __future__ import annotations
from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable
from lsp_client.utils.jsonrpc import jsonrpc_uuid
from lsp_client.utils.types import lsp_type
from lsp_client.protocol import LSPCapabilityClientProtocol, LSPWorkspaceCapabilityProtocol

@runtime_checkable
class WithRequestWorkspaceX(
    LSPWorkspaceCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return ("workspace/x",)

    @override
    @classmethod
    def register_workspace_capability(
        cls, cap: lsp_type.WorkspaceClientCapabilities
    ) -> None:
        # Declare client support per spec
        pass

    @override
    @classmethod
    def check_server_capability(
        cls,
        cap: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ) -> None:
        assert cap.workspace_x_provider

    async def request_workspace_x(self, query: str) -> lsp_type.WorkspaceXResponse | None:
        return await self._request(
            lsp_type.WorkspaceXRequest(
                id=jsonrpc_uuid(),
                params=lsp_type.WorkspaceXParams(query=query),
            ),
            schema=lsp_type.WorkspaceXResponse,
        )
```

## 测试仓库策略（重要）

为降低维护成本并提高覆盖面，测试系统采用“少量大型测试仓库”而非为每一特定场景单独新建仓库的策略：

- 使用 2–3 个较大的 Python 测试仓库（fixtures），在同一仓库内覆盖多种 capability 与场景：
  - `monorepo_core`：无错误主路径，覆盖 Definition/References、跨包导入、类/函数/泛型、装饰器、别名等常见用例（参考 src/lsp_client/capability/request/definition.py:39-51, 83-119 与 src/lsp_client/capability/request/reference.py:30-65）。
  - `monorepo_errors`：集中触发多类型诊断，包括类型不匹配、未定义名称、不可达代码、DiagnosticTag 与 RelatedInformation（参考 src/lsp_client/capability/response/publish_diagnostics.py:51-58）。
  - `monorepo_multi_root`：验证多根工作区下的 `as_uri`/`from_uri` 行为与跨根引用（参考 src/lsp_client/client/abc.py:174-201, 203-206, 288-309）。

- 每个仓库包含一个统一的 `anchors.json`，声明定义点（`def_`）、引用点（`ref_`）与错误点（`err_`）的文件与位置（行、列），测试根据 anchors 自动定位请求位置。

- 集成测试以 Pyright 为基准：
  - Definition/References：在 `monorepo_core` 上对锚点发送请求，比对黄金快照。
  - Diagnostics：在 `monorepo_errors` 上打开文件并收集诊断，归一化后比对黄金快照；如需断言可在测试中重载客户端的 `receive_publish_diagnostics` 方法。

- 快照归一化与稳定性：
  - 将返回结果中的 URI 统一为工作区相对路径；剔除不稳定字段（版本、随机 token、时间戳）。
  - 对 `Diagnostic` 仅保留核心属性：`range`、`severity`、`code`、`message`、`source`、`tags`。

- 运行与选择器：
  - 单元与能力层使用 `-m unit`、`-m capabilities`，快速执行。
  - 集成层使用 `-m 'integration and pyright'`，本地有 `pyright-langserver` 则运行，否则跳过或使用 Docker。

该策略允许在少量仓库内通过锚点与模块组合来覆盖更多协议与真实场景，显著减少样例碎片化与维护成本。

### Server Request/Notification Template

```python
from __future__ import annotations
from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable
import lsprotocol.types as lsp_type
from lsp_client.protocol import LSPCapabilityClientProtocol, LSPWindowCapabilityProtocol

@runtime_checkable
class WithReceiveX(
    LSPWindowCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return ("window/x",)

    @override
    @classmethod
    def register_window_capability(cls, cap: lsp_type.WindowClientCapabilities) -> None:
        pass

    @override
    @classmethod
    def check_server_capability(
        cls,
        cap: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ) -> None:
        return

    async def receive_x(self, req: lsp_type.XNotification) -> None:
        # Handle server notification
        ...

@runtime_checkable
class WithRespondX(
    LSPWindowCapabilityProtocol,
    LSPCapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return ("window/xRequest",)

    @override
    @classmethod
    def register_window_capability(cls, cap: lsp_type.WindowClientCapabilities) -> None:
        pass

    @override
    @classmethod
    def check_server_capability(
        cls,
        cap: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ) -> None:
        return

    async def respond_x(self, req: lsp_type.XRequest) -> lsp_type.XResponse:
        # Return response object
        return lsp_type.XResponse(id=req.id, result=...)
```

Add a `match` branch for the new capability in the server request dispatch function to handle deserialization and response sending.

## Default Capabilities

Optionally mix in `WithDefaultCapabilities` to enable baseline capabilities (logging and text document synchronization).

---

## Your Contribution Makes a Difference

Implementing LSP capabilities is at the heart of this project. Each capability you add:

- **Enables new use cases** for developers building intelligent tools
- **Improves compatibility** across different language servers
- **Advances the Python ecosystem** by making LSP more accessible

The LSP specification is vast, and we can't cover it all alone. Your expertise—whether it's understanding debugger protocols, refactoring operations, or any other LSP feature—is invaluable.

**Questions or stuck on something?** Don't hesitate to open an issue or discussion. We're here to help guide you through the process!

Thank you for contributing to lsp-client! 🎉
