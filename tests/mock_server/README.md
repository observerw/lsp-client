# MockLSPServer

A comprehensive Mock LSP Server implementation for testing LSP clients.

## Overview

`MockLSPServer` 是一个仿照 `LSPClientBase` 设计思路实现的模拟 LSP 服务器，专门用于测试 LSP 客户端。它允许你：

- 自定义服务器能力 (capabilities)
- 配置模拟响应 (mock responses)
- 模拟各种 LSP 方法的行为
- 进行完整的 LSP 通信协议测试

## 主要特性

### 1. 灵活的响应提供器系统

- **StaticResponseProvider**: 提供预定义的静态响应
- **CallbackResponseProvider**: 使用回调函数动态生成响应
- **可扩展的架构**: 轻松添加自定义响应提供器

### 2. 完整的 LSP 协议支持

- 标准 LSP 初始化流程
- 文档同步 (textDocument/didOpen, didChange, didClose)
- 支持所有常见的 LSP 方法
- 正确的 JSON-RPC 消息格式

### 3. 预配置的便利服务器

- `create_hover_mock_server()`: 提供悬停信息
- `create_completion_mock_server()`: 提供代码补全
- `create_definition_mock_server()`: 提供定义跳转

## 使用示例

### 基本用法

```python
import asyncio
from mock_server import MockLSPServer

async def basic_example():
    # 创建一个基本的模拟服务器
    server = MockLSPServer()
    
    # 添加静态响应
    server.add_static_responses({
        "textDocument/hover": {
            "contents": {
                "kind": "markdown", 
                "value": "Mock hover content"
            }
        }
    })
    
    # 测试响应生成
    response = server._generate_response("textDocument/hover", {
        "textDocument": {"uri": "file:///test.py"},
        "position": {"line": 1, "character": 5}
    })
    print(response)

asyncio.run(basic_example())
```

### 使用预配置服务器

```python
from mock_server import create_completion_mock_server

# 创建一个提供代码补全的模拟服务器
server = create_completion_mock_server([
    "my_function", 
    "my_variable", 
    "MyClass"
])

# 测试补全
response = server._generate_response("textDocument/completion", {
    "textDocument": {"uri": "file:///test.py"},
    "position": {"line": 10, "character": 5}
})
print(response)
```

### 自定义能力和响应

```python
from lsprotocol import types
from mock_server import MockLSPServer

# 自定义服务器能力
custom_capabilities = types.ServerCapabilities(
    text_document_sync=types.TextDocumentSyncOptions(
        open_close=True,
        change=types.TextDocumentSyncKind.Incremental,
    ),
    hover_provider=True,
    completion_provider=types.CompletionOptions(
        trigger_characters=[".", "->"],
        resolve_provider=True,
    ),
    definition_provider=True,
)

server = MockLSPServer(server_capabilities=custom_capabilities)

# 添加自定义回调响应
def handle_custom_hover(method: str, params: dict | None) -> dict:
    if not params:
        return {"contents": "No information"}
    
    position = params.get("position", {})
    line = position.get("line", 0)
    
    return {
        "contents": {
            "kind": "markdown",
            "value": f"**Custom hover** at line {line}"
        }
    }

server.add_callback_responses({
    "textDocument/hover": handle_custom_hover
})
```

### 作为独立 LSP 服务器运行

```python
# 保存为 my_mock_server.py
import asyncio
from mock_server import MockLSPServer

async def main():
    server = MockLSPServer()
    
    # 配置你的响应...
    
    # 作为标准 LSP 服务器运行
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

然后可以在命令行中运行：
```bash
python my_mock_server.py
```

## API 参考

### MockLSPServer

主要的模拟服务器类。

```python
class MockLSPServer:
    def __init__(
        self, 
        server_capabilities: types.ServerCapabilities = ...,
        response_providers: list[MockResponseProvider] = ...,
        server_info: types.ServerInfo = ...
    )
```

#### 方法

- `add_response_provider(provider: MockResponseProvider)`: 添加响应提供器
- `add_static_responses(responses: Mapping[str, dict])`: 添加静态响应
- `add_callback_responses(callbacks: Mapping[str, RequestHandler])`: 添加回调响应
- `run()`: 作为 LSP 服务器运行（处理标准输入输出）

### 响应提供器

#### StaticResponseProvider

```python
provider = StaticResponseProvider(responses={
    "textDocument/hover": {"contents": "Static hover"},
    "textDocument/completion": {"items": []}
})
```

#### CallbackResponseProvider

```python
def my_handler(method: str, params: dict | None) -> Any:
    # 自定义逻辑
    return {"result": "custom response"}

provider = CallbackResponseProvider(callbacks={
    "textDocument/hover": my_handler
})
```

### 便利函数

- `create_hover_mock_server(hover_content: str)`: 创建悬停服务器
- `create_completion_mock_server(completion_items: list[str])`: 创建补全服务器  
- `create_definition_mock_server(definition_uri: str)`: 创建定义服务器

## 设计思路

`MockLSPServer` 的设计借鉴了 `LSPClientBase` 的架构：

1. **模块化能力系统**: 类似客户端的 capability mixins，服务器使用响应提供器来模块化功能
2. **异步架构**: 完全异步的设计，支持并发处理
3. **类型安全**: 使用 `lsprotocol.types` 确保类型正确性
4. **可扩展性**: 容易添加新的 LSP 方法支持

## 测试用例

运行测试来验证功能：

```bash
cd tests
python test_mock_server.py
```

## 配置文件支持

MockLSPServer 支持通过 JSON 配置文件进行配置：

```json
{
  "responses": {
    "textDocument/hover": {
      "contents": {
        "kind": "markdown",
        "value": "Configured hover content"
      }
    },
    "textDocument/completion": {
      "items": [
        {
          "label": "configured_item",
          "kind": 1,
          "insertText": "configured_item"
        }
      ]
    }
  }
}
```

```bash
python mock_server.py --config config.json
```

## 注意事项

1. **消息格式**: 使用标准的 LSP JSON-RPC 协议格式
2. **错误处理**: 自动处理未知方法并返回适当的错误响应
3. **文档同步**: 自动跟踪打开的文档状态
4. **日志记录**: 支持详细的调试日志记录

这个 MockLSPServer 可以帮助你全面测试 LSP 客户端的各种功能，确保客户端能够正确处理各种服务器响应。
