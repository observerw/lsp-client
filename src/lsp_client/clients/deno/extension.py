from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, override, runtime_checkable

from loguru import logger

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import (
    CapabilityClientProtocol,
    CapabilityProtocol,
    ExperimentalCapabilityProtocol,
    ServerNotificationHook,
    ServerRequestHookProtocol,
    ServerRequestHookRegistry,
)
from lsp_client.utils.types import AnyPath, lsp_type

from .models import (
    DENO_CACHE,
    DENO_PERFORMANCE,
    DENO_REGISTRY_STATE,
    DENO_RELOAD_IMPORT_REGISTRIES,
    DENO_TASK,
    DENO_TEST_MODULE,
    DENO_TEST_MODULE_DELETE,
    DENO_TEST_RUN,
    DENO_TEST_RUN_CANCEL,
    DENO_TEST_RUN_PROGRESS,
    DENO_VIRTUAL_TEXT_DOCUMENT,
    DenoCacheParams,
    DenoCacheRequest,
    DenoCacheResponse,
    DenoPerformanceRequest,
    DenoPerformanceResponse,
    DenoRegistryStatusNotification,
    DenoReloadImportRegistriesRequest,
    DenoReloadImportRegistriesResponse,
    DenoTaskRequest,
    DenoTaskResponse,
    DenoTestModuleDeleteNotification,
    DenoTestModuleNotification,
    DenoTestRunCancelParams,
    DenoTestRunCancelRequest,
    DenoTestRunCancelResponse,
    DenoTestRunProgressNotification,
    DenoTestRunRequest,
    DenoTestRunRequestParams,
    DenoTestRunResponse,
    DenoTestRunResponseParams,
    DenoVirtualTextDocumentParams,
    DenoVirtualTextDocumentRequest,
    DenoVirtualTextDocumentResponse,
)


@runtime_checkable
class WithRequestDenoCache(
    CapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (DENO_CACHE,)

    async def request_deno_cache(
        self,
        referrer: AnyPath,
        uris: Sequence[AnyPath] = (),
    ) -> None:
        return await self.request(
            DenoCacheRequest(
                id=jsonrpc_uuid(),
                params=DenoCacheParams(
                    referrer=lsp_type.TextDocumentIdentifier(uri=self.as_uri(referrer)),
                    uris=[
                        lsp_type.TextDocumentIdentifier(uri=self.as_uri(uri))
                        for uri in uris
                    ],
                ),
            ),
            schema=DenoCacheResponse,
        )


@runtime_checkable
class WithRequestDenoPerformance(
    CapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (DENO_PERFORMANCE,)

    async def request_deno_performance(self) -> Any:
        return await self.request(
            DenoPerformanceRequest(id=jsonrpc_uuid()),
            schema=DenoPerformanceResponse,
        )


@runtime_checkable
class WithRequestDenoReloadImportRegistries(
    CapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (DENO_RELOAD_IMPORT_REGISTRIES,)

    async def request_deno_reload_import_registries(self) -> None:
        return await self.request(
            DenoReloadImportRegistriesRequest(id=jsonrpc_uuid()),
            schema=DenoReloadImportRegistriesResponse,
        )


@runtime_checkable
class WithRequestDenoVirtualTextDocument(
    CapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (DENO_VIRTUAL_TEXT_DOCUMENT,)

    async def request_deno_virtual_text_document(
        self,
        uri: str,
    ) -> str:
        return await self.request(
            DenoVirtualTextDocumentRequest(
                id=jsonrpc_uuid(),
                params=DenoVirtualTextDocumentParams(
                    text_document=lsp_type.TextDocumentIdentifier(uri=uri)
                ),
            ),
            schema=DenoVirtualTextDocumentResponse,
        )


@runtime_checkable
class WithRequestDenoTask(
    CapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (DENO_TASK,)

    async def request_deno_task(self) -> list[Any]:
        return await self.request(
            DenoTaskRequest(id=jsonrpc_uuid()),
            schema=DenoTaskResponse,
        )


@runtime_checkable
class WithRequestDenoTestRun(
    ExperimentalCapabilityProtocol,
    CapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (DENO_TEST_RUN,)

    @override
    @classmethod
    def register_experimental_capability(cls, cap: dict[str, Any]) -> None:
        cap["testingApi"] = True

    async def request_deno_test_run(
        self,
        params: DenoTestRunRequestParams,
    ) -> DenoTestRunResponseParams:
        return await self.request(
            DenoTestRunRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=DenoTestRunResponse,
        )


@runtime_checkable
class WithRequestDenoTestRunCancel(
    CapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (DENO_TEST_RUN_CANCEL,)

    async def request_deno_test_run_cancel(
        self,
        test_run_id: int,
    ) -> None:
        return await self.request(
            DenoTestRunCancelRequest(
                id=jsonrpc_uuid(),
                params=DenoTestRunCancelParams(id=test_run_id),
            ),
            schema=DenoTestRunCancelResponse,
        )


@runtime_checkable
class WithReceiveDenoRegistryStatus(
    ServerRequestHookProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (DENO_REGISTRY_STATE,)

    async def receive_deno_registry_state(
        self, noti: DenoRegistryStatusNotification
    ) -> None:
        logger.debug("Received Deno registry state: {}", noti.params)

    @override
    def register_server_request_hooks(
        self, registry: ServerRequestHookRegistry
    ) -> None:
        super().register_server_request_hooks(registry)
        registry.register(
            DENO_REGISTRY_STATE,
            ServerNotificationHook(
                cls=DenoRegistryStatusNotification,
                execute=self.receive_deno_registry_state,
            ),
        )


@runtime_checkable
class WithReceiveDenoTestModule(
    ServerRequestHookProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (DENO_TEST_MODULE,)

    async def receive_deno_test_module(self, noti: DenoTestModuleNotification) -> None:
        logger.debug("Received Deno test module: {}", noti.params)

    @override
    def register_server_request_hooks(
        self, registry: ServerRequestHookRegistry
    ) -> None:
        super().register_server_request_hooks(registry)
        registry.register(
            DENO_TEST_MODULE,
            ServerNotificationHook(
                cls=DenoTestModuleNotification,
                execute=self.receive_deno_test_module,
            ),
        )


@runtime_checkable
class WithReceiveDenoTestModuleDelete(
    ServerRequestHookProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (DENO_TEST_MODULE_DELETE,)

    async def receive_deno_test_module_delete(
        self, noti: DenoTestModuleDeleteNotification
    ) -> None:
        logger.debug("Received Deno test module delete: {}", noti.params)

    @override
    def register_server_request_hooks(
        self, registry: ServerRequestHookRegistry
    ) -> None:
        super().register_server_request_hooks(registry)
        registry.register(
            DENO_TEST_MODULE_DELETE,
            ServerNotificationHook(
                cls=DenoTestModuleDeleteNotification,
                execute=self.receive_deno_test_module_delete,
            ),
        )


@runtime_checkable
class WithReceiveDenoTestRunProgress(
    ServerRequestHookProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (DENO_TEST_RUN_PROGRESS,)

    async def receive_deno_test_run_progress(
        self, noti: DenoTestRunProgressNotification
    ) -> None:
        logger.debug("Received Deno test run progress: {}", noti.params)

    @override
    def register_server_request_hooks(
        self, registry: ServerRequestHookRegistry
    ) -> None:
        super().register_server_request_hooks(registry)
        registry.register(
            DENO_TEST_RUN_PROGRESS,
            ServerNotificationHook(
                cls=DenoTestRunProgressNotification,
                execute=self.receive_deno_test_run_progress,
            ),
        )
