from __future__ import annotations

from os import PathLike
from pathlib import Path
from typing import override


class RelPath(Path):
    """Guarantees the path to be relative."""

    def __init__(
        self,
        *args: str | PathLike[str],
        base_path: str | PathLike | None = None,
    ) -> None:
        if (path := Path(*args)).is_absolute():
            if not base_path:
                raise ValueError("base_path must be provided for absolute paths")
            if not (base_path := Path(base_path)).is_absolute():
                raise ValueError("base_path must be an absolute path")
            super().__init__(path.relative_to(base_path))
        else:
            super().__init__(path)

    def as_path(self) -> Path:
        return Path(self)

    @override
    def absolute(self) -> AbsPath:
        return AbsPath(super().absolute())

    @override
    def resolve(self, strict: bool = False) -> AbsPath:
        return AbsPath(self.as_path().resolve(strict))

    def absolute_to(self, base_path: str | PathLike) -> AbsPath:
        return AbsPath(self, base_path=base_path)


class AbsPath(Path):
    """Guarantees the path to be absolute."""

    def __init__(
        self,
        *args: str | PathLike[str],
        base_path: str | PathLike | None = None,
    ) -> None:
        if (path := Path(*args)).is_absolute():
            super().__init__(path)
        else:
            if not base_path:
                raise ValueError("base_path must be provided for relative paths")
            if not (base_path := Path(base_path)).is_absolute():
                raise ValueError("base_path must be an absolute path")

            super().__init__(base_path / path)

    def as_path(self) -> Path:
        return Path(self)

    @override
    def relative_to(
        self,
        other: str | PathLike,
        /,
        *_deprecated: str | PathLike,
        walk_up: bool = False,
    ) -> RelPath:
        return RelPath(self, base_path=Path(other))
