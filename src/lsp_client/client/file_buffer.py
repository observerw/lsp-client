from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from functools import cached_property

from lsp_client.utils.path import AbsPath


@dataclass(frozen=True)
class LSPFileBufferItem:
    file_path: AbsPath

    @cached_property
    def uri(self) -> str:
        return self.file_path.as_uri()

    @cached_property
    def contents(self) -> str:
        return self.file_path.read_text(encoding="utf-8")

    @property
    def version(self) -> int:
        # TODO: when text editing is supported, this should be updated
        return 0


class LSPFileBuffer:
    type PosixPath = str

    _lookup: dict[PosixPath, LSPFileBufferItem] = field(default_factory=dict)
    _ref_count: Counter[PosixPath] = field(default_factory=Counter)

    def open(self, file_paths: Iterable[AbsPath]) -> Sequence[LSPFileBufferItem]:
        """Open files and save to buffer. Only return newly opened files."""

        self._ref_count.update(file_path.as_posix() for file_path in file_paths)

        items: list[LSPFileBufferItem] = []
        for file_path in file_paths:
            if (file_path_posix := file_path.as_posix()) in self._lookup:
                continue

            item = self._lookup[file_path_posix] = LSPFileBufferItem(
                file_path=file_path,
            )
            items.append(item)

        return items

    def close(self, file_paths: Iterable[AbsPath]) -> Sequence[AbsPath]:
        """
        Close the files. Return paths of files that are really closed (ref count reaches 0).
        """

        closed_files: list[AbsPath] = []

        self._ref_count.subtract(path.as_posix() for path in file_paths)
        for path, ref_count in self._ref_count.items():
            if ref_count > 0:
                continue

            closed_files.append(AbsPath(path))
            self._lookup.pop(path, None)

        return closed_files
