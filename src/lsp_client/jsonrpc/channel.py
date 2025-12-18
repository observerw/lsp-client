# one shot channel for response
from __future__ import annotations

from lsp_client.utils.channel import (
    OneShotReceiver,
    OneShotSender,
    OneShotTable,
    oneshot_channel,
)

from .types import RawResponsePackage

response_channel = oneshot_channel[RawResponsePackage]
type RespSender = OneShotSender[RawResponsePackage]
type RespReceiver = OneShotReceiver[RawResponsePackage]

# table for response dispatch
ResponseTable = OneShotTable[RawResponsePackage]
