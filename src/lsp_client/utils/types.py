from __future__ import annotations

import os
from typing import Protocol

from attrs import AttrsInstance
from lsprotocol import types as lsp_type

Position = lsp_type.Position
Range = lsp_type.Range

AnyPath = str | os.PathLike[str]

type Request = AttrsInstance
type Notification = AttrsInstance


class Response[T](Protocol):
    """
    Duck-type schema for extracting the result type from `lsprotocol` Response schema.
    """

    result: T
