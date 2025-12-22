import {
	LocalServer,
	LSPClient,
	SyncFeature,
	DefinitionFeature,
	toURI,
} from "../src";
import { resolve } from "path";

class RustClient extends LSPClient {
	public sync = new SyncFeature();
	public definition = new DefinitionFeature();

	constructor(server: LocalServer) {
		super(server);
		this.registerFeature(this.sync);
		this.registerFeature(this.definition);
	}

	protected getLanguageId() {
		return "rust";
	}
	protected createInitializationOptions() {
		return {
			"rust-analyzer": {
				checkOnSave: false,
			},
		};
	}
}

async function run() {
	// Ensure rust-analyzer is in your PATH
	const server = new LocalServer(["rust-analyzer"]);
	const client = new RustClient(server);

	for await (const lsp of client.start()) {
		const uri = toURI(resolve("src/main.rs"));

		await lsp.sync.didOpen(
			lsp,
			uri,
			"rust",
			'fn main() { let x = 5; println!("{}", x); }',
		);

		console.log('Requesting definition of "x"...');
		const def = await lsp.definition.getDefinition(lsp, uri, 0, 31);
		console.log("Definition:", JSON.stringify(def, null, 2));
	}
}

run().catch(console.error);
