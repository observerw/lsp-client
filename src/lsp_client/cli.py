from __future__ import annotations

import typer

app = typer.Typer(help="LSP Client CLI")


@app.command()
def hover(
    path: str = typer.Argument(..., help="Path to the file"),
    line: int = typer.Argument(..., help="Line number (0-indexed)"),
    character: int = typer.Argument(..., help="Character position (0-indexed)"),
):
    """
    Request hover information at a given position.
    """
    typer.echo(f"Hover at {path}:{line}:{character}")
    raise typer.Exit()


@app.command()
def definition(
    path: str = typer.Argument(..., help="Path to the file"),
    line: int = typer.Argument(..., help="Line number (0-indexed)"),
    character: int = typer.Argument(..., help="Character position (0-indexed)"),
):
    """
    Go to definition.
    """
    typer.echo(f"Definition at {path}:{line}:{character}")
    raise typer.Exit()


@app.command()
def references(
    path: str = typer.Argument(..., help="Path to the file"),
    line: int = typer.Argument(..., help="Line number (0-indexed)"),
    character: int = typer.Argument(..., help="Character position (0-indexed)"),
):
    """
    Find references.
    """
    typer.echo(f"References at {path}:{line}:{character}")
    raise typer.Exit()


@app.command()
def implementation(
    path: str = typer.Argument(..., help="Path to the file"),
    line: int = typer.Argument(..., help="Line number (0-indexed)"),
    character: int = typer.Argument(..., help="Character position (0-indexed)"),
):
    """
    Find implementations.
    """
    typer.echo(f"Implementation at {path}:{line}:{character}")
    raise typer.Exit()


@app.command(name="type-definition")
def type_definition(
    path: str = typer.Argument(..., help="Path to the file"),
    line: int = typer.Argument(..., help="Line number (0-indexed)"),
    character: int = typer.Argument(..., help="Character position (0-indexed)"),
):
    """
    Find type definition.
    """
    typer.echo(f"Type definition at {path}:{line}:{character}")
    raise typer.Exit()


@app.command()
def symbols(
    path: str = typer.Argument(..., help="Path to the file"),
):
    """
    List document symbols.
    """
    typer.echo(f"Symbols in {path}")
    raise typer.Exit()


@app.command(name="workspace-symbols")
def workspace_symbols(
    query: str = typer.Argument(..., help="Search query for workspace symbols"),
):
    """
    Search for workspace symbols.
    """
    typer.echo(f"Workspace symbols for query: {query}")
    raise typer.Exit()


@app.command()
def rename(
    path: str = typer.Argument(..., help="Path to the file"),
    line: int = typer.Argument(..., help="Line number (0-indexed)"),
    character: int = typer.Argument(..., help="Character position (0-indexed)"),
    new_name: str = typer.Argument(..., help="The new name for the symbol"),
):
    """
    Rename a symbol.
    """
    typer.echo(f"Rename at {path}:{line}:{character} to {new_name}")
    raise typer.Exit()


if __name__ == "__main__":
    app()
