import { type ClientCapabilities } from "vscode-languageserver-protocol";
import type { LSPFeature, LSPClient } from "../client/abc";

export class SyncFeature implements LSPFeature {
	public fillClientCapabilities(caps: ClientCapabilities): void {
		caps.textDocument = caps.textDocument || {};
		caps.textDocument.synchronization = {
			willSave: true,
			willSaveWaitUntil: true,
			didSave: true,
		};
	}

	public async didOpen(
		client: LSPClient,
		uri: string,
		languageId: string,
		text: string,
	) {
		await client.sendNotification("textDocument/didOpen", {
			textDocument: {
				uri,
				languageId,
				version: 0,
				text,
			},
		});
	}

	public async didClose(client: LSPClient, uri: string) {
		await client.sendNotification("textDocument/didClose", {
			textDocument: {
				uri,
			},
		});
	}
}
