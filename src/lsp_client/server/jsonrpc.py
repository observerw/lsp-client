from __future__ import annotations

import json
import re
from asyncio import StreamReader, StreamWriter

from lsp_client import jsonrpc

HEADER_RE = re.compile(r"Content-Length:\s*(?P<length>\d+)\r\n")
"""match lsp header line: `Content-Length: ...\r\n`"""


async def read_raw_package(reader: StreamReader) -> jsonrpc.RawPackage:
    # when process is closed, the reader will always return b''
    if not (header_bytes := await reader.readline()):
        raise EOFError("LSP server process closed")

    header = header_bytes.decode("utf-8")
    header_match = HEADER_RE.match(header)
    if not header_match or not (length := int(header_match.group("length"))):
        raise ValueError("Invalid LSP response header")

    await reader.readline()  # consume '\r\n'

    body_bytes = await reader.readexactly(length)
    return json.loads(body_bytes.decode("utf-8"))


async def write_raw_package(writer: StreamWriter, package: jsonrpc.RawPackage) -> None:
    dumped = jsonrpc.package_serialize(package).encode("utf-8")
    length = len(dumped)

    header = f"Content-Length: {length}\r\n\r\n".encode()
    writer.write(header + dumped)
    # will trigger BrokenPipeError if the process is closed
    await writer.drain()
