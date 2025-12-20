from __future__ import annotations

from typing import Any, Literal

import cattrs
from attrs import define, field, resolve_types
from lsprotocol import converters

from lsp_client.jsonrpc.id import ID
from lsp_client.utils.types import lsp_type

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
class DenoTestData:
    id: str
    label: str
    steps: list[DenoTestData] | None = None
    range: lsp_type.Range | None = None


@define
class DenoTestIdentifier:
    text_document: lsp_type.TextDocumentIdentifier
    id: str | None = None
    step_id: str | None = None


@define
class DenoTestMessage:
    message: lsp_type.MarkupContent
    expected_output: str | None = None
    actual_output: str | None = None
    location: lsp_type.Location | None = None


@define
class DenoTestEnqueuedStartedSkipped:
    type: Literal["enqueued", "started", "skipped"]
    test: DenoTestIdentifier


@define
class DenoTestFailedErrored:
    type: Literal["failed", "errored"]
    test: DenoTestIdentifier
    messages: list[DenoTestMessage]
    duration: float | None = None


@define
class DenoTestPassed:
    type: Literal["passed"]
    test: DenoTestIdentifier
    duration: float | None = None


@define
class DenoTestOutput:
    type: Literal["output"]
    value: str
    test: DenoTestIdentifier | None = None
    location: lsp_type.Location | None = None


@define
class DenoTestEnd:
    type: Literal["end"]


type DenoTestRunProgressMessage = (
    DenoTestEnqueuedStartedSkipped
    | DenoTestFailedErrored
    | DenoTestPassed
    | DenoTestOutput
    | DenoTestEnd
)


@define
class DenoEnqueuedTestModule:
    text_document: lsp_type.TextDocumentIdentifier
    ids: list[str]


# ---------------------------------- Requests --------------------------------- #


@define
class DenoCacheParams:
    referrer: lsp_type.TextDocumentIdentifier
    uris: list[lsp_type.TextDocumentIdentifier] = field(factory=list)


@define
class DenoCacheRequest:
    id: ID
    params: DenoCacheParams
    method: Literal["deno/cache"] = DENO_CACHE
    jsonrpc: str = "2.0"


@define
class DenoCacheResponse:
    id: ID | None
    result: None
    jsonrpc: str = "2.0"


@define
class DenoPerformanceRequest:
    id: ID
    method: Literal["deno/performance"] = DENO_PERFORMANCE
    jsonrpc: str = "2.0"


@define
class DenoPerformanceResponse:
    id: ID | None
    result: Any
    jsonrpc: str = "2.0"


@define
class DenoReloadImportRegistriesRequest:
    id: ID
    method: Literal["deno/reloadImportRegistries"] = DENO_RELOAD_IMPORT_REGISTRIES
    jsonrpc: str = "2.0"


@define
class DenoReloadImportRegistriesResponse:
    id: ID | None
    result: None
    jsonrpc: str = "2.0"


@define
class DenoVirtualTextDocumentParams:
    text_document: lsp_type.TextDocumentIdentifier


@define
class DenoVirtualTextDocumentRequest:
    id: ID
    params: DenoVirtualTextDocumentParams
    method: Literal["deno/virtualTextDocument"] = DENO_VIRTUAL_TEXT_DOCUMENT
    jsonrpc: str = "2.0"


@define
class DenoVirtualTextDocumentResponse:
    id: ID | None
    result: str
    jsonrpc: str = "2.0"


@define
class DenoTaskParams:
    pass


@define
class DenoTaskRequest:
    id: ID
    params: DenoTaskParams | None = None
    method: Literal["deno/task"] = DENO_TASK
    jsonrpc: str = "2.0"


@define
class DenoTaskResponse:
    id: ID | None
    result: list[Any]
    jsonrpc: str = "2.0"


@define
class DenoTestRunRequestParams:
    id: int
    kind: Literal["run", "coverage", "debug"]
    exclude: list[DenoTestIdentifier] | None = None
    include: list[DenoTestIdentifier] | None = None


@define
class DenoTestRunRequest:
    id: ID
    params: DenoTestRunRequestParams
    method: Literal["deno/testRun"] = DENO_TEST_RUN
    jsonrpc: str = "2.0"


@define
class DenoTestRunResponseParams:
    enqueued: list[DenoEnqueuedTestModule]


@define
class DenoTestRunResponse:
    id: ID | None
    result: DenoTestRunResponseParams
    jsonrpc: str = "2.0"


@define
class DenoTestRunCancelParams:
    id: int


@define
class DenoTestRunCancelRequest:
    id: ID
    params: DenoTestRunCancelParams
    method: Literal["deno/testRunCancel"] = DENO_TEST_RUN_CANCEL
    jsonrpc: str = "2.0"


@define
class DenoTestRunCancelResponse:
    id: ID | None
    result: None
    jsonrpc: str = "2.0"


# -------------------------------- Notifications ------------------------------- #


@define
class DenoRegistryStatusNotificationParams:
    origin: str
    suggestions: bool


@define
class DenoRegistryStatusNotification:
    params: DenoRegistryStatusNotificationParams
    method: Literal["deno/registryState"] = DENO_REGISTRY_STATE
    jsonrpc: str = "2.0"


@define
class DenoTestModuleParams:
    text_document: lsp_type.TextDocumentIdentifier
    kind: Literal["insert", "replace"]
    label: str
    tests: list[DenoTestData]


@define
class DenoTestModuleNotification:
    params: DenoTestModuleParams
    method: Literal["deno/testModule"] = DENO_TEST_MODULE
    jsonrpc: str = "2.0"


@define
class DenoTestModuleDeleteParams:
    text_document: lsp_type.TextDocumentIdentifier


@define
class DenoTestModuleDeleteNotification:
    params: DenoTestModuleDeleteParams
    method: Literal["deno/testModuleDelete"] = DENO_TEST_MODULE_DELETE
    jsonrpc: str = "2.0"


@define
class DenoTestRunProgressParams:
    id: int
    message: DenoTestRunProgressMessage


@define
class DenoTestRunProgressNotification:
    params: DenoTestRunProgressParams
    method: Literal["deno/testRunProgress"] = DENO_TEST_RUN_PROGRESS
    jsonrpc: str = "2.0"


def register_hooks(converter: cattrs.Converter) -> None:
    resolve_types(DenoTestData)
    resolve_types(DenoTestIdentifier)
    resolve_types(DenoTestMessage)
    resolve_types(DenoTestEnqueuedStartedSkipped)
    resolve_types(DenoTestFailedErrored)
    resolve_types(DenoTestPassed)
    resolve_types(DenoTestOutput)
    resolve_types(DenoTestEnd)
    resolve_types(DenoEnqueuedTestModule)
    resolve_types(DenoCacheParams)
    resolve_types(DenoCacheRequest)
    resolve_types(DenoCacheResponse)
    resolve_types(DenoPerformanceRequest)
    resolve_types(DenoPerformanceResponse)
    resolve_types(DenoReloadImportRegistriesRequest)
    resolve_types(DenoReloadImportRegistriesResponse)
    resolve_types(DenoVirtualTextDocumentParams)
    resolve_types(DenoVirtualTextDocumentRequest)
    resolve_types(DenoVirtualTextDocumentResponse)
    resolve_types(DenoTaskParams)
    resolve_types(DenoTaskRequest)
    resolve_types(DenoTaskResponse)
    resolve_types(DenoTestRunRequestParams)
    resolve_types(DenoTestRunRequest)
    resolve_types(DenoTestRunResponseParams)
    resolve_types(DenoTestRunResponse)
    resolve_types(DenoTestRunCancelParams)
    resolve_types(DenoTestRunCancelRequest)
    resolve_types(DenoTestRunCancelResponse)
    resolve_types(DenoRegistryStatusNotificationParams)
    resolve_types(DenoRegistryStatusNotification)
    resolve_types(DenoTestModuleParams)
    resolve_types(DenoTestModuleNotification)
    resolve_types(DenoTestModuleDeleteParams)
    resolve_types(DenoTestModuleDeleteNotification)
    resolve_types(DenoTestRunProgressParams)
    resolve_types(DenoTestRunProgressNotification)

    def _test_run_progress_message_hook(
        obj: Any, _: type
    ) -> DenoTestRunProgressMessage:
        if not isinstance(obj, dict):
            return obj

        match obj.get("type"):
            case "enqueued" | "started" | "skipped":
                return converter.structure(obj, DenoTestEnqueuedStartedSkipped)
            case "failed" | "errored":
                return converter.structure(obj, DenoTestFailedErrored)
            case "passed":
                return converter.structure(obj, DenoTestPassed)
            case "output":
                return converter.structure(obj, DenoTestOutput)
            case "end":
                return converter.structure(obj, DenoTestEnd)
            case _:
                raise ValueError(
                    f"Unknown DenoTestRunProgressMessage type: {obj.get('type')}"
                )

    converter.register_structure_hook(
        DenoTestRunProgressMessage, _test_run_progress_message_hook
    )


register_hooks(converters.get_converter())
