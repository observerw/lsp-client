# Add a New LSP Capability

When adding a new capability, you will be given a link to the LSP specification of the capability.

## Check compatibility

To ensure that the capability is compatible with both the client and server, you must implement the `check_client_capability` and `check_server_capability` methods according to the specification. For example:

```python
@runtime_checkable
class WithRequestInlineCompletions(LSPCapabilityClient, Protocol):
    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.inline_completion

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert capability.inline_completion_provider
```

## Add Docstring

Add comprehensive docstring with LSP specification link. For example:

```python
@runtime_checkable
class WithRequestHover(LSPCapabilityClient, Protocol):
    """
    `textDocument/hover` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_hover
    """
```

## Design API

Principles for designing the API:

- Only ask for minimum required parameters, and make other parameters as keyword-only arguments with default values.
- Make reasonable defaults for parameters.

## Return Value

### Regular

For most capabilities, the return result is a single type named `types.*Result`. You should return the underlying type directly. For example:

```python
HoverResult = Union[Hover, None]

@runtime_checkable
class WithRequestHover(LSPCapabilityClient, Protocol):
    async def request_hover(
        self, file_path: AnyPath, position: Position
    ) -> types.Hover | None: # return underlying type directly
        ...
```

### Union of Multiple Types

For some capabilities, the return result is a union of multiple types, for example:

```python
InlineCompletionResult = Union[
    InlineCompletionList, Sequence[InlineCompletionItem], None
]

@attrs.define
class InlineCompletionList:
    items: Sequence["InlineCompletionItem"] = attrs.field()
```

Notice that `InlineCompletionList` is same as `Sequence[InlineCompletionItem]`, but with a wrapper class. From the perspective of the user experience, it is better to return a consistent format. **You must check the return type and determine the best way to return the result**. For example:

```python
@runtime_checkable
class WithRequestInlineCompletions(LSPCapabilityClient, Protocol):
    async def request_inline_completions(
        self,
        file_path: AnyPath,
        position: Position,
    ) -> Sequence[types.InlineCompletionItem] | None:
        match await self.request(
            types.InlineCompletionRequest(
                // ...
            )
        ):
            case types.InlineCompletionList(items=items):
                return items # extract items from InlineCompletionList
            case list() as items:
                return items # already a list of InlineCompletionItem
            case None:
                return None
```

For some capabilities, the return type is not a single type, but a union of multiple types. In this case, you should define separate classes for each type and return the appropriate type based on the request. For example:

## Implementation Patterns

### Basic Pattern

The basic pattern for implementing a capability includes:

1. **Class Declaration**: Use `@runtime_checkable` decorator and inherit from `LSPCapabilityClient` and `Protocol`
2. **Docstring**: Include LSP specification link
3. **Capability Checks**: Implement both client and server capability checks
4. **Request Method**: Implement the main request method with proper typing

```python
@runtime_checkable
class WithRequestHover(LSPCapabilityClient, Protocol):
    """
    `textDocument/hover` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_hover
    """

    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.hover

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert capability.hover_provider

    async def request_hover(
        self, file_path: AnyPath, position: Position
    ) -> types.Hover | None:
        return await self.request(
            types.HoverRequest(
                id=jsonrpc_uuid(),
                params=types.HoverParams(
                    text_document=types.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                ),
            ),
            schema=types.HoverResponse,
        )
```

### Base Class Pattern

For capabilities with multiple variants (e.g., different return types), create a base class with shared logic:

```python
@runtime_checkable
class WithRequestDefinitionBase(LSPCapabilityClient, Protocol):
    @override
    @classmethod
    def check_client_capability(cls):
        assert (text_document := cls.client_capabilities.text_document)
        assert text_document.definition

    @override
    @classmethod
    def check_server_capability(cls, capability: types.ServerCapabilities):
        assert capability.definition_provider

    async def _request_definition(
        self, file_path: AnyPath, position: Position
    ) -> types.DefinitionResult:
        return await self.request(
            types.DefinitionRequest(
                id=jsonrpc_uuid(),
                params=types.DefinitionParams(
                    text_document=types.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                ),
            ),
            schema=types.DefinitionResponse,
        )

@runtime_checkable
class WithRequestDefinitionLocation(WithRequestDefinitionBase, Protocol):
    """
    `textDocument/definition` - Location variant
    """

    @staticmethod
    def is_locations(result: list) -> TypeGuard[list[types.Location]]:
        return all(isinstance(item, types.Location) for item in result)

    async def request_definition_location(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[types.Location] | None:
        match await self._request_definition(file_path, position):
            case types.Location() as location:
                return [location]
            case list() as locations if self.is_locations(locations):
                return locations
```

### TypeGuard Pattern

Use `TypeGuard` for type checking with union return types:

```python
@staticmethod
def is_locations(result: list) -> TypeGuard[list[types.Location]]:
    return all(isinstance(item, types.Location) for item in result)
```

### Match-Case Pattern

Use pattern matching for handling different return types:

```python
match await self.request(...):
    case types.CompletionList(items=items) | items:
        return items
    case types.Location() as location:
        return [location]
    case list() as locations if self.is_locations(locations):
        return locations
    case None:
        return None
```

## Common Parameters

### Text Document Operations

Most text document operations require:

- `file_path: AnyPath` - Path to the file
- `position: Position` - Position in the document

### Workspace Operations

Workspace operations typically require:

- `query: str` - Search query or command

### Request Construction

Always include:

- `id=jsonrpc_uuid()` - Unique request ID
- `params=` - Request parameters object
- `schema=` - Response schema for validation

## Error Handling

The base client handles errors automatically. Focus on:

1. Proper capability checks
2. Correct parameter construction
3. Appropriate return type handling

## Testing

When implementing a new capability, ensure:

1. Both client and server capability checks work
2. Request parameters are correctly constructed
3. Response handling covers all possible return types
4. TypeGuards work correctly for union types
