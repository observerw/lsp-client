from __future__ import annotations

from os import PathLike
from pathlib import Path
from typing import override


class RelPath(Path):
    """Guarantees the path to be relative to a base path."""

    base_path: Path | None = None

    def __init__(self, *args, base_path: Path | None = None) -> None:
        path = Path(*args)

        if path.is_absolute():
            if not base_path:
                raise ValueError("RelPath must be relative or provide a base_path")
            super().__init__(path.relative_to(base_path))
        else:
            super().__init__(path)

        self.base_path = base_path

    def absolute(self) -> AbsPath:
        return AbsPath(super().absolute())

    def resolve(self, strict: bool = False) -> AbsPath:
        return AbsPath(super().resolve(strict))


class AbsPath(Path):
    """Guarantees the path to be absolute."""

    def __init__(self, *args, base_path: Path | None = None) -> None:
        path = Path(*args)

        if not path.is_absolute():
            if not base_path:
                super().__init__(path.absolute())
            else:
                super().__init__(base_path.absolute(), path)
        else:
            super().__init__(path)

    @override
    def relative_to(
        self,
        other: str | PathLike,
        /,
        *_deprecated: str | PathLike,
        walk_up: bool = False,
    ) -> RelPath:
        return RelPath(
            super().relative_to(other, *_deprecated, walk_up=walk_up),
            base_path=Path(other),
        )
