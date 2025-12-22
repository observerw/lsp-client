import {
	type ClientCapabilities,
	type Definition,
	type LocationLink,
} from "vscode-languageserver-protocol";
import type { LSPFeature, LSPClient } from "../client/abc";

export class DefinitionFeature implements LSPFeature {
	public fillClientCapabilities(caps: ClientCapabilities): void {
		caps.textDocument = caps.textDocument || {};
		caps.textDocument.definition = {
			dynamicRegistration: false,
			linkSupport: true,
		};
	}

	public async getDefinition(
		client: LSPClient,
		uri: string,
		line: number,
		character: number,
	): Promise<Definition | LocationLink[] | null> {
		return await client.sendRequest("textDocument/definition", {
			textDocument: { uri },
			position: { line, character },
		});
	}
}
