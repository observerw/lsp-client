from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, override, runtime_checkable

import attrs

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import CapabilityClientProtocol, TextDocumentCapabilityProtocol
from lsp_client.utils.types import AnyPath, Position, lsp_type


@runtime_checkable
class WithRequestSignatureHelp(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/signatureHelp` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_signatureHelp
    """

    @override
    @classmethod
    def methods(cls) -> Sequence[str]:
        return (lsp_type.TEXT_DOCUMENT_SIGNATURE_HELP,)

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        cap.signature_help = lsp_type.SignatureHelpClientCapabilities(
            context_support=True,
            signature_information=lsp_type.ClientSignatureInformationOptions(
                documentation_format=[
                    lsp_type.MarkupKind.Markdown,
                    lsp_type.MarkupKind.PlainText,
                ],
                parameter_information=lsp_type.ClientSignatureParameterInformationOptions(
                    label_offset_support=True,
                ),
                active_parameter_support=True,
            ),
        )

    @override
    @classmethod
    def check_server_capability(
        cls,
        cap: lsp_type.ServerCapabilities,
        info: lsp_type.ServerInfo | None,
    ) -> None:
        super().check_server_capability(cap, info)
        assert cap.signature_help_provider

    async def request_signature_help(
        self,
        file_path: AnyPath,
        position: Position,
        *,
        trigger_character: str | None = None,
        is_retrigger: bool | None = None,
        active_signature_help: lsp_type.SignatureHelp | None = None,
        trigger_kind: lsp_type.SignatureHelpTriggerKind | None = None,
    ) -> lsp_type.SignatureHelp | None:
        if is_retrigger is None:
            is_retrigger = active_signature_help is not None

        if trigger_kind is None:
            trigger_kind = (
                lsp_type.SignatureHelpTriggerKind.TriggerCharacter
                if trigger_character is not None
                else lsp_type.SignatureHelpTriggerKind.Invoked
            )

        context = lsp_type.SignatureHelpContext(
            trigger_kind=trigger_kind,
            trigger_character=trigger_character,
            is_retrigger=is_retrigger,
            active_signature_help=active_signature_help,
        )

        return await self.file_request(
            lsp_type.SignatureHelpRequest(
                id=jsonrpc_uuid(),
                params=lsp_type.SignatureHelpParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                    context=context,
                ),
            ),
            schema=lsp_type.SignatureHelpResponse,
            file_paths=[file_path],
        )

    async def request_active_signature(
        self,
        file_path: AnyPath,
        position: Position,
        *,
        trigger_character: str | None = None,
        active_signature_help: lsp_type.SignatureHelp | None = None,
    ) -> lsp_type.SignatureInformation | None:
        """
        Request the signature help and return the currently active signature.

        The `active_parameter` of the returned signature is automatically resolved:
        it prefers the `active_parameter` from the top-level `SignatureHelp` response
        over the one defined in `SignatureInformation`, following the LSP specification.
        """

        res = await self.request_signature_help(
            file_path,
            position,
            trigger_character=trigger_character,
            active_signature_help=active_signature_help,
        )
        if not res or not res.signatures:
            return None

        sig_idx = res.active_signature if res.active_signature is not None else 0
        if not (0 <= sig_idx < len(res.signatures)):
            sig_idx = 0

        sig = res.signatures[sig_idx]
        active_param = (
            res.active_parameter
            if res.active_parameter is not None
            else sig.active_parameter
        )

        return attrs.evolve(sig, active_parameter=active_param)
