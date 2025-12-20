# Deno LSP Custom Capabilities

This document summarizes the custom LSP capabilities and protocol extensions provided by the Deno Language Server.

## Custom Requests (Client → Server)

| Request                       | Purpose                                                                                                                   |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `deno/cache`                  | Instructs Deno to cache a module and its dependencies. Usually sent as a response to a code action for un-cached modules. |
| `deno/performance`            | Requests timing averages for Deno's internal instrumentation for monitoring and debugging.                                |
| `deno/reloadImportRegistries` | Reloads cached responses from import registries.                                                                          |
| `deno/virtualTextDocument`    | Requests read-only virtual text documents (e.g., cached remote modules or Deno library files) using the `deno:` schema.   |
| `deno/task`                   | Retrieves a list of available Deno tasks defined in `deno.json` or `deno.jsonc`.                                          |

## Custom Notifications (Server → Client)

| Notification         | Purpose                                                                                                      |
| -------------------- | ------------------------------------------------------------------------------------------------------------ |
| `deno/registryState` | Notifies the client about import registry discovery status, providing suggestions for configuration updates. |

## Testing API (Experimental)

Requires `experimental.testingApi` capability to be enabled by both client and server.

### Requests (Client → Server)

- `deno/testRun`: Initiates a test execution for specified modules or tests.
- `deno/testRunCancel`: Cancels an ongoing test run by ID.

### Notifications (Server → Client)

- `deno/testModule`: Sent when a test module is discovered.
- `deno/testModuleDelete`: Sent when a test module is deleted.
- `deno/testRunProgress`: Tracks the progress and state of a test run (`enqueued`, `started`, `passed`, `failed`, etc.).

## Other Experimental Capabilities

- `denoConfigTasks`: Support for tasks defined in Deno configuration files.
- `didRefreshDenoConfigurationTreeNotifications`: Notifications for when the configuration tree is refreshed.
