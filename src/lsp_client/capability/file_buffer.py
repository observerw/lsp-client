from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from functools import cached_property, partial

import aiometer
import anyio
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

    async def open(self, file_uris: Iterable[str]) -> Sequence[LSPFileBufferItem]:
        """Open files and save to buffer. Only return newly opened files."""

        self._ref_count.update(file_uris)

        async def map_item(uri: str) -> LSPFileBufferItem:
            text = await anyio.Path(from_local_uri(uri)).read_bytes()
            return LSPFileBufferItem(
                file_uri=uri,
                file_content=text,
            )

        file_uris = [uri for uri in file_uris if uri not in self._lookup]
        items = await aiometer.run_all(
            [partial(map_item, uri) for uri in file_uris],
        )
        self._lookup.update({item.file_uri: item for item in items})

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
