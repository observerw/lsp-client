# (WIP) LSP Client

[![PyPI version](https://badge.fury.io/py/lsp-client.svg)](https://badge.fury.io/py/lsp-client)
[![Python versions](https://img.shields.io/pypi/pyversions/lsp-client.svg)](https://pypi.org/project/lsp-client/)

> [!WARNING]
> This project is still in development and may not be fully functional yet. Soon we will have a stable release.

Full-featured, well-typed, and easy-to-use LSP client for Python.

## Features

- **Well-Typed**: Provides type hints and [protocol definition](<README#Requiring LSP Client to Have Desired Capabilities>) for all LSP operations, making it easy to use and integrate with your code.
- **Full-Featured**: Supports a wide range of LSP capabilities, and you can easily [extend it to support more capabilities](<README#(Advanced) Add Support for New LSP Capabilities>).
- **Multiprocessing Support**: Supports [running multiple LSP servers in parallel](<README#Multiple Server Processes>), allowing you to speedup your LSP operations.
- **Easy to Extend**: You can easily [add support for new LSP servers](<README#Add Support for New LSP Servers>) by implementing a few methods.

## Install

```bash
uv add lsp-client
```

Currently, `lsp-client` supports Python 3.13 and above. Any backward-compatible PRs are welcome.

To maintain simplicity, `lsp-client` won't automatically install any LSP servers. Before using it, you need to install the LSP server you want to use and make sure it is available in your `$PATH`. Here are some examples of LSP servers you can use:

- Python: [BasedPyright](https://docs.basedpyright.com/dev/installation/command-line-and-language-server/)

## Usage

```python
import asyncio as aio
from lsp_client import Position
from lsp_client.servers.based_pyright import BasedPyrightClient

async def main():
    async with BasedPyrightClient.start(
        repo_path="/path/to/your/repo",  # Update with your repo path
        server_count=1,  # adjust it to start more servers if needed
        # set server process info if needed
        server_info=LSPServerInfo(env={"EXAMPLE_ENV_VAR": "value"}),
    ) as client:
        # Request references for a symbol at a specific position
        refs = await client.request_references(
            file_path="path/to/your/file.py",  # Update with your file path
            position=Position(12, 29),  # Update with your desired position
        )
        # [Task-Group](https://docs.python.org/3/library/asyncio-task.html#asyncio.TaskGroup)-like interface
        # to run multiple requests in parallel
        def_tasks = [
            client.create_request(client.request_definition(file_path, position))
            for file_path, position in [
                ("path/to/your/file1.py", Position(10, 5)),
                ("path/to/your/file2.py", Position(20, 15)),
            ]
        ]

    for ref in refs or []:
        print(ref)
    
    for def_result in [task.result() for task in def_tasks]:
        print(def_result)


if __name__ == "__main__":
    aio.run(main())
```

### A work-as-is Example

Clone the repository and run the following example to see how it works:

```bash
git clone https://github.com/observerw/lsp-client.git && cd lsp-client
uv sync
```

```python
from pathlib import Path

from asyncio_addon import async_main

from lsp_client import Position, Range, lsp_type
from lsp_client.servers.based_pyright import BasedPyrightClient

repo_path = Path.cwd()
curr_path = Path(__file__)


@async_main
async def main():
    async with BasedPyrightClient.start(repo_path=repo_path) as client:
        # found all references of `BasedPyrightClient` class
        if refs := await client.request_references(
            file_path="src/lsp_client/servers/based_pyright.py",
            position=Position(8, 24),
        ):
            for ref in refs:
                print(f"Found references: {ref}")

            # check if includes reference in current file
            assert any(
                client.from_uri(ref.uri) == curr_path
                and ref.range == Range(Position(13, 15), Position(13, 33))
                for ref in refs
            )
            print("All references found successfully.")

        # find the definition of `main` function
        def_task = client.create_request(
            client.request_definition_location(
                file_path=curr_path,
                position=Position(47, 8),
            )
        )

    match def_task.result():
        case [lsp_type.Location() as loc]:
            print(f"Found definition: {loc}")
            assert client.from_uri(loc.uri) == curr_path
            assert loc.range == Range(Position(12, 10), Position(12, 14))
    print("Definition found successfully.")


if __name__ == "__main__":
    main()
```

## Multiple Server Processes

One key feature of `lsp-client` is the ability to **run multiple LSP server processes in parallel**. This is particularly useful for large codebases or when you need to perform multiple LSP requests simultaneously, which can significantly speed up operations like finding references or definitions.

For example:

```python
async with BasedPyrightClient.start(
    repo_path="/path/to/repo",
    server_count=4,  # Start 4 parallel server processes
) as client:
    # Now requests can be processed in parallel across 4 servers
    tasks = [
        client.create_request(client.request_references(file, position))
        for file, position in file_position_pairs
    ]
# all task results will be available here
results = [task.result() for task in tasks]
```

When a request is made by the client, it will be sent to one of the available server processes. The client will automatically do load balancing among the server processes.

However, please note that **starting too many server processes may consume a lot of system resources and lead to performance degradation**. It is recommended to adjust the `server_count` parameter based on your system's capabilities and the request count you expect to handle.

## Requiring LSP Client to Have Desired Capabilities

All LSP capabilities are declared as [`Protocol`](https://typing.python.org/en/latest/spec/protocol.html), which means you can combine them to create a protocol to constrain the LSP client to have specific capabilities. For example:

```python
# Client with references and definition capabilities
class GoodClient(
    lsp_cap.WithRequestReferences,
    lsp_cap.WithRequestDefinition,
    LSPClientBase,
): ...

# Client with only completions capability
class BadClient(
    lsp_cap.WithRequestCompletions,
    LSPClientBase,
): ...

# Here we define a protocol that requires the client
# to have both `WithRequestReferences` and `WithRequestDefinition` capabilities.
@runtime_checkable
class DesiredClientProtocol(
    lsp_cap.WithRequestReferences,
    lsp_cap.WithRequestDefinition,
    Protocol, # don't forget to inherit from `Protocol`
): ...

# good client can be accepted
good: type[DesiredClientProtocol] = GoodClient

# bad client cannot be accepted, since it does not have the required capabilities
# type[BadClient]  is not assignable to type[DesiredClientProtocol]
bad: type[DesiredClientProtocol] = BadClient
```

## Add Support for New LSP Servers

Add support for a new LSP server is simple. Example from [BasedPyright](src/lsp_client/servers/based_pyright.py):

```python
# We define a new LSP client for BasedPyright
class BasedPyrightClient(
    # we can add capabilities as needed
    cap.WithRequestReferences,
    cap.WithRequestDefinition,
    cap.WithRequestHover,
    # ...
    LSPClientBase,  # Remember to inherit from LSPClientBase
):
    # language_id which this client supports, required
    language_id: ClassVar = lsp_types.LanguageKind.Python
    # start command to launch the LSP server, required
    # note that the command must start a stdio server
    server_cmd: ClassVar = (
        "basedpyright-langserver",
        "--stdio",
    )
    client_capabilities: ClassVar[types.ClientCapabilities] = types.ClientCapabilities(
        # ... client capabilities specific to BasedPyright ...
    )
```

That's it! Provide some necessary information and you are good to go.

## (WIP) Static Mode

If you are performing static code analysis, consider set `static=True` when starting the client. This will benefit you from caching the results of LSP requests.

In static mode, it is required to keep the code repository unchanged during the analysis. That means:

- You should not modify the code files while the client is running.
- All code-modifying LSP requests (like `textDocument/didChange`) will be banned and raised as an error.

## (WIP) Automatic Document Synchronization

Coming soon!

## (Advanced) Add Support for New LSP Capabilities

TODO ...

## What if ... ?

### What if the default capability implementation does not work for my LSP server?

If the default capability implementation doesn't work for your LSP server, you can override the specific methods in your client implementation. For example:

```python
class MyCustomClient(
    cap.WithRequestReferences,
    LSPClientBase, 
):
    # ... other implementation ...
    
    @override
    async def request_references(
        self, file_path: AnyPath, position: Position
    ) -> types.ReferencesResult:
        # Custom implementation for your LSP server
        # that differs from the default behavior
        return await self.request(
            types.ReferencesRequest(
                id=jsonrpc_uuid(),
                params=types.ReferenceParams(
                    # Custom parameters for your server
                    context=types.ReferenceContext(include_declaration=True),  # Different default
                    text_document=types.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                ),
            ),
            schema=types.ReferencesResponse,
        )
```

You can override any capability method to customize the behavior for your specific LSP server requirements.

## Why Do We ... ?

### Why do we need this project?

`multilspy` is great, but extending it needs some extra works, including:

- Support for more LSP servers
- Support for more LSP capabilities
- Support for parallel LSP server processes
- Provide better type hints and documentation
- ...

This project takes the spirit of `multilspy`, and refactor the code to provide more out-of-the-box support for various LSP servers (we even support [Github Copilot Server](src/lsp_client/servers/copilot.py)) and capabilities, and **make it easier to extend and use**.

### (Static Mode) Why do we need to use Language Server to perform static code analysis?

It seems weird to use a language server for static code analysis, since it is highly dynamic and requires a daemon to run. In an ideal world, we would have a nice static analysis tool that can analyze the code and export the results, so we can just use these results without needing a running server.

However, the truth is almost all static analysis tools are far from satisfying. For example, for Python:

- [pycallgraph](https://github.com/gak/pycallgraph) is archived long ago and [py-call-graph](https://github.com/Lewiscowles1986/py-call-graph) mainly focuses on call graph visualization.
- Github's [stack-graph](https://github.com/github/stack-graphs) seems cool, but it is mainly focused on name resolution (i.e. `textDocument/definition`) and does not provide a full static analysis solution.
- [LSIF](https://lsif.dev/) is dead, and its successor [scip](https://github.com/sourcegraph/scip-python) is not being actively maintained.

On contrast, LSP servers are usually well-maintained (since they are used by many IDEs), and they provide a lot of useful features for static code analysis, such as find references, find definitions, hover information, and more.

Sadly, most LSP servers are designed for dynamic analysis and do not provide cache mechanism, which means they will be slow when performing code analysis on large codebases. But considering their rich features and good maintainability, it is a good trade-off.

### Why do we have `WithRequestDocumentSymbols`, `WithRequestDocumentSymbolInformation`, and `WithRequestDocumentBaseSymbols` for `textDocument/documentSymbol` capability?

According to the [LSP specification](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_documentSymbol), LSP servers should return `SymbolInformation[]` whenever possible. However, some LSP servers do not support this feature and only return `DocumentSymbol[]`, so the return type of `WithRequestDocumentSymbols` is `Sequence[types.DocumentSymbolInformation] | Sequence[types.DocumentSymbol]`, which can be troublesome when you want to use the return values:

```python
for sym in await client.request_document_symbols(file_path):
    # type matching is required here, boring!
    if isinstance(sym, types.DocumentSymbolInformation):
        print(f"Symbol: {sym.name} at {sym.location.range}")
    elif isinstance(sym, types.DocumentSymbol):
        print(f"Document Symbol: {sym.name} at {sym.range}")
```

To make it easier to use, we provide `WithRequestDocumentSymbolInformation` that returns `Sequence[types.DocumentSymbolInformation]` only and `WithRequestDocumentBaseSymbols` that returns `Sequence[types.DocumentSymbol]` only. If you can ensure that your LSP server supports `SymbolInformation`, you can use `WithRequestDocumentSymbolInformation` to get a more convenient return type.

This design is also applied to:

- `WithRequestDefinition`
- `WithRequestWorkspaceSymbols`

## Thanks

This project is heavily inspired by [multilspy](https://github.com/microsoft/multilspy), thanks for their great work!
