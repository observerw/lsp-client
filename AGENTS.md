# AGENTS.md

## Development Commands

- Lint & format: `ruff check --fix && ruff format`
- Type checking: `mypy src/`
- Run all tests: `pytest`
- Run single test: `pytest path/to/test.py::test_function`
- Run integration tests: `pytest -m integration`
- Run pyright tests: `pytest -m pyright`

## Code Style Guidelines

- Python: 3.12+ required, use `from __future__ import annotations`
- Imports: Use isort (handled by ruff), group stdlib, third-party, local imports
- Formatting: Double quotes, space indentation (handled by ruff format)
- Types: Full type annotations required, use `lsp_type` alias for LSP types
- Naming: snake_case for variables/functions, PascalCase for classes
- Error handling: Use tenacity for retries, anyio.fail_after for timeouts
- Async: Use async/await, asyncer.TaskGroup for concurrency
- Structure: Follow capability-based protocol pattern in capability/ module