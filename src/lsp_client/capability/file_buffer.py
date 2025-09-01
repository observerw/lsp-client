from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from functools import cached_property

from attrs import Factory, define, frozen

from lsp_client.utils.path import AbsPath, from_local_uri


@frozen
class LSPFileBufferItem:
    file_uri: str
    file_content: bytes

    @cached_property
    def file_path(self) -> AbsPath:
        return from_local_uri(self.file_uri)

    @cached_property
    def content(self) -> str:
        return self.file_content.decode("utf-8")

    @property
    def version(self) -> int:
        # TODO: when text editing is supported, this should be updated
        return 0


@define
class LSPFileBuffer:
    _lookup: dict[str, LSPFileBufferItem] = Factory(dict)
    _ref_count: Counter[str] = Factory(Counter)

    def open(self, file_uris: Iterable[str]) -> Sequence[LSPFileBufferItem]:
        """Open files and save to buffer. Only return newly opened files."""

        self._ref_count.update(file_uris)

        items: list[LSPFileBufferItem] = []
        for uri in file_uris:
            if uri in self._lookup:
                continue

            item = self._lookup[uri] = LSPFileBufferItem(
                file_uri=uri,
                file_content=from_local_uri(uri).read_bytes(),
            )
            items.append(item)

        return items

    def close(self, file_uris: Iterable[str]) -> Sequence[LSPFileBufferItem]:
        """
        Close the files. Return paths of files that are really closed (ref count reaches 0).
        """

        self._ref_count.subtract(file_uris)

        closed_items: list[LSPFileBufferItem] = []
        for uri, ref_count in self._ref_count.items():
            if ref_count > 0:
                continue
            if item := self._lookup.pop(uri, None):
                closed_items.append(item)

        return closed_items
