# Configuration Management

The `lsp-client` SDK provides a robust and flexible way to manage Language Server Protocol (LSP) configurations. It supports global settings, path-based overrides, and automatic synchronization with the server.

## ConfigurationMap

The `ConfigurationMap` is the central utility for managing settings. It implements a tiered configuration logic similar to "User Settings" vs. "Workspace Settings" in popular IDEs.

### Core Features

- **Global Config**: Default settings applied to all files.
- **Scoped Overrides**: High-priority settings applied to files matching specific Glob patterns (e.g., `**/tests/**`).
- **Deep Merging**: Nested dictionaries are merged recursively, ensuring that partial updates don't wipe out unrelated settings.
- **Auto-Sync**: Automatically notifies the server when configurations change.

### Basic Usage

```python
from lsp_client.utils.config import ConfigurationMap
from lsp_client.clients.pyright import PyrightClient

# 1. Initialize the map
config_map = ConfigurationMap()

# 2. Set global configurations
config_map.update_global({
    "python": {
        "analysis": {
            "typeCheckingMode": "basic",
            "autoImportCompletions": True
        }
    }
})

# 3. Add path-specific overrides
# For example, disable type checking for the tests directory
config_map.add_scope(
    pattern="**/tests/**",
    config={
        "python": {
            "analysis": {
                "typeCheckingMode": "off"
            }
        }
    }
)
```

## Integrating with the Client

To enable configuration support, assign your `config_map` to the client's `configuration_map` attribute.

```python
async with PyrightClient(workspace=Path.cwd()) as client:
    client.configuration_map = config_map
    # The SDK will now handle 'workspace/configuration' requests automatically
```

## Automatic Synchronization

One of the most powerful features is **Automatic Sync**. If your client supports the `workspace/didChangeConfiguration` capability (standard in most built-in clients like `PyrightClient`), the SDK will automatically notify the server whenever you update the `ConfigurationMap`.

### How it Works

1. You update the `config_map` using `update_global` or `add_scope`.
2. The SDK detects the change and sends a `workspace/didChangeConfiguration` notification to the server.
3. The server, upon receiving the notification, typically clears its cache and requests fresh configuration from the client.

```python
# Updating config at runtime
config_map.update_global({"python.analysis.typeCheckingMode": "strict"})

# The server is automatically notified and will see the "strict" mode immediately.
```

## Advanced: Change Listeners

You can register custom listeners to react to configuration changes. Listeners must follow the `ConfigurationChangeListener` protocol.

```python
def my_listener(config_map, **kwargs):
    reason = kwargs.get("reason", "unknown")
    print(f"Config changed! Reason: {reason}")

config_map.on_change(my_listener)

# Pass context to your listeners
config_map.update_global({"setting": True}, reason="User Preference Update")
```

## Implementation Details

### Merge Strategy
When a file matches multiple scope patterns, configurations are merged in the order they were added. The merge is **deep**, meaning:

```python
# Base
{"a": {"b": 1, "c": 2}}
# Update
{"a": {"b": 3}}
# Result
{"a": {"b": 3, "c": 2}}  # "c" is preserved
```

### Path Resolution
The `scope_uri` provided by the server is automatically converted to a local filesystem path before pattern matching, allowing you to use standard Glob patterns.
