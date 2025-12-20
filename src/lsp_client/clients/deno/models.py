from __future__ import annotations

from typing import Any, Literal

from attrs import define, field
from lsprotocol import types as lsp_type

from lsp_client.jsonrpc.id import ID

# ---------------------------------- Constants --------------------------------- #

DENO_CACHE: Literal["deno/cache"] = "deno/cache"
DENO_PERFORMANCE: Literal["deno/performance"] = "deno/performance"
DENO_RELOAD_IMPORT_REGISTRIES: Literal["deno/reloadImportRegistries"] = (
    "deno/reloadImportRegistries"
)
DENO_VIRTUAL_TEXT_DOCUMENT: Literal["deno/virtualTextDocument"] = (
    "deno/virtualTextDocument"
)
DENO_TASK: Literal["deno/task"] = "deno/task"
DENO_REGISTRY_STATE: Literal["deno/registryState"] = "deno/registryState"
DENO_TEST_RUN: Literal["deno/testRun"] = "deno/testRun"
DENO_TEST_RUN_CANCEL: Literal["deno/testRunCancel"] = "deno/testRunCancel"
DENO_TEST_MODULE: Literal["deno/testModule"] = "deno/testModule"
DENO_TEST_MODULE_DELETE: Literal["deno/testModuleDelete"] = "deno/testModuleDelete"
DENO_TEST_RUN_PROGRESS: Literal["deno/testRunProgress"] = "deno/testRunProgress"


# --------------------------------- Base Types -------------------------------- #


@define
class TestData:
    id: str
    label: str
    steps: list[TestData] | None = None
    range: lsp_type.Range | None = None


@define
class TestIdentifier:
    text_document: lsp_type.TextDocumentIdentifier
    id: str | None = None
    step_id: str | None = None


@define
class TestMessage:
    message: lsp_type.MarkupContent
    expected_output: str | None = None
    actual_output: str | None = None
    location: lsp_type.Location | None = None


@define
class TestEnqueuedStartedSkipped:
    type: Literal["enqueued", "started", "skipped"]
    test: TestIdentifier


@define
class TestFailedErrored:
    type: Literal["failed", "errored"]
    test: TestIdentifier
    messages: list[TestMessage]
    duration: float | None = None


@define
class TestPassed:
    type: Literal["passed"]
    test: TestIdentifier
    duration: float | None = None


@define
class TestOutput:
    type: Literal["output"]
    value: str
    test: TestIdentifier | None = None
    location: lsp_type.Location | None = None


@define
class TestEnd:
    type: Literal["end"]


type TestRunProgressMessage = (
    TestEnqueuedStartedSkipped | TestFailedErrored | TestPassed | TestOutput | TestEnd
)


@define
class EnqueuedTestModule:
    text_document: lsp_type.TextDocumentIdentifier
    ids: list[str]


# ---------------------------------- Requests --------------------------------- #


@define
class CacheParams:
    referrer: lsp_type.TextDocumentIdentifier
    uris: list[lsp_type.TextDocumentIdentifier] = field(factory=list)


@define
class CacheRequest:
    id: ID
    params: CacheParams
    method: Literal["deno/cache"] = DENO_CACHE
    jsonrpc: str = "2.0"


@define
class CacheResponse:
    id: ID | None
    result: None
    jsonrpc: str = "2.0"


@define
class VirtualTextDocumentParams:
    text_document: lsp_type.TextDocumentIdentifier


@define
class VirtualTextDocumentRequest:
    id: ID
    params: VirtualTextDocumentParams
    method: Literal["deno/virtualTextDocument"] = DENO_VIRTUAL_TEXT_DOCUMENT
    jsonrpc: str = "2.0"


@define
class VirtualTextDocumentResponse:
    id: ID | None
    result: str
    jsonrpc: str = "2.0"


@define
class TaskParams:
    pass


@define
class TaskRequest:
    id: ID
    params: TaskParams | None = None
    method: Literal["deno/task"] = DENO_TASK
    jsonrpc: str = "2.0"


@define
class TaskResponse:
    id: ID | None
    result: list[Any]
    jsonrpc: str = "2.0"


@define
class TestRunRequestParams:
    id: int
    kind: Literal["run", "coverage", "debug"]
    exclude: list[TestIdentifier] | None = None
    include: list[TestIdentifier] | None = None


@define
class TestRunRequest:
    id: ID
    params: TestRunRequestParams
    method: Literal["deno/testRun"] = DENO_TEST_RUN
    jsonrpc: str = "2.0"


@define
class TestRunResponseParams:
    enqueued: list[EnqueuedTestModule]


@define
class TestRunResponse:
    id: ID | None
    result: TestRunResponseParams
    jsonrpc: str = "2.0"


@define
class TestRunCancelParams:
    id: int


@define
class TestRunCancelRequest:
    id: ID
    params: TestRunCancelParams
    method: Literal["deno/testRunCancel"] = DENO_TEST_RUN_CANCEL
    jsonrpc: str = "2.0"


@define
class TestRunCancelResponse:
    id: ID | None
    result: None
    jsonrpc: str = "2.0"


# -------------------------------- Notifications ------------------------------- #


@define
class RegistryStatusNotificationParams:
    origin: str
    suggestions: bool


@define
class RegistryStatusNotification:
    params: RegistryStatusNotificationParams
    method: Literal["deno/registryState"] = DENO_REGISTRY_STATE
    jsonrpc: str = "2.0"


@define
class TestModuleParams:
    text_document: lsp_type.TextDocumentIdentifier
    kind: Literal["insert", "replace"]
    label: str
    tests: list[TestData]


@define
class TestModuleNotification:
    params: TestModuleParams
    method: Literal["deno/testModule"] = DENO_TEST_MODULE
    jsonrpc: str = "2.0"


@define
class TestModuleDeleteParams:
    text_document: lsp_type.TextDocumentIdentifier


@define
class TestModuleDeleteNotification:
    params: TestModuleDeleteParams
    method: Literal["deno/testModuleDelete"] = DENO_TEST_MODULE_DELETE
    jsonrpc: str = "2.0"


@define
class TestRunProgressParams:
    id: int
    message: TestRunProgressMessage


@define
class TestRunProgressNotification:
    params: TestRunProgressParams
    method: Literal["deno/testRunProgress"] = DENO_TEST_RUN_PROGRESS
    jsonrpc: str = "2.0"
