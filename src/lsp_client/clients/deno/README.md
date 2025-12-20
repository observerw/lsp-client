# Deno LSP Custom Capabilities

This document summarizes the custom LSP capabilities and protocol extensions provided by the Deno Language Server.

## Custom Requests (Client → Server)

| Request                       | Python Method                           | Purpose                                                                                                                   |
| ----------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `deno/cache`                  | `request_deno_cache`                    | Instructs Deno to cache a module and its dependencies. Usually sent as a response to a code action for un-cached modules. |
| `deno/performance`            | `request_deno_performance`              | Requests timing averages for Deno's internal instrumentation for monitoring and debugging.                                |
| `deno/reloadImportRegistries` | `request_deno_reload_import_registries` | Reloads cached responses from import registries.                                                                          |
| `deno/virtualTextDocument`    | `request_deno_virtual_text_document`    | Requests read-only virtual text documents (e.g., cached remote modules or Deno library files) using the `deno:` schema.   |
| `deno/task`                   | `request_deno_task`                     | Retrieves a list of available Deno tasks defined in `deno.json` or `deno.jsonc`.                                          |

## Custom Notifications (Server → Client)

| Notification         | Python Method                 | Default Behavior                                                                   |
| -------------------- | ----------------------------- | ---------------------------------------------------------------------------------- |
| `deno/registryState` | `receive_deno_registry_state` | Logs the registry discovery status and configuration suggestions at `DEBUG` level. |

## Testing API (Experimental)

Requires `experimental.testingApi` capability to be enabled by both client and server.

### Requests (Client → Server)

| Request              | Python Method                  | Purpose                                                    |
| -------------------- | ------------------------------ | ---------------------------------------------------------- |
| `deno/testRun`       | `request_deno_test_run`        | Initiates a test execution for specified modules or tests. |
| `deno/testRunCancel` | `request_deno_test_run_cancel` | Cancels an ongoing test run by ID.                         |

### Notifications (Server → Client)

| Notification            | Python Method                     | Default Behavior                                                                           |
| ----------------------- | --------------------------------- | ------------------------------------------------------------------------------------------ |
| `deno/testModule`       | `receive_deno_test_module`        | Logs discovered test module information at `DEBUG` level.                                  |
| `deno/testModuleDelete` | `receive_deno_test_module_delete` | Logs deleted test module information at `DEBUG` level.                                     |
| `deno/testRunProgress`  | `receive_deno_test_run_progress`  | Logs test run state (`enqueued`, `started`, `passed`, etc.) and progress at `DEBUG` level. |

## Other Experimental Capabilities

- `denoConfigTasks`: Support for tasks defined in Deno configuration files.
- `didRefreshDenoConfigurationTreeNotifications`: Notifications for when the configuration tree is refreshed.

## Deno LSP Documentation

### Official Documentation

- [Language Server Integration](https://docs.deno.com/runtime/reference/lsp_integration/) - Comprehensive guide for integrating with Deno's LSP, including custom capabilities and testing API
- [deno lsp CLI Reference](https://docs.deno.com/runtime/reference/cli/lsp/) - Basic information about the `deno lsp` subcommand
- [Deno & Visual Studio Code](https://docs.deno.com/runtime/reference/vscode/) - Complete integration guide and setup

### Source Code & Development

- [Deno CLI LSP Source](https://github.com/denoland/deno/tree/main/cli/lsp) - The actual LSP implementation in Rust
- [VS Code Extension](https://github.com/denoland/vscode_deno) - Official VS Code extension source code
