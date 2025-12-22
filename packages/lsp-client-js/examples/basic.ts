import {
	LocalServer,
	LSPClient,
	SyncFeature,
	HoverFeature,
	toURI,
} from "../src";
import { resolve } from "path";

// 1. Define your custom client with the features you need
class SimplePythonClient extends LSPClient {
	public sync = new SyncFeature();
	public hover = new HoverFeature();

	constructor(server: LocalServer) {
		super(server);
		this.registerFeature(this.sync);
		this.registerFeature(this.hover);
	}

	protected getLanguageId() {
		return "python";
	}
	protected createInitializationOptions() {
		return {};
	}
}

async function run() {
	// 2. Setup the server (ensure pyright is installed: npm install -g pyright)
	const server = new LocalServer(["pyright-langserver", "--stdio"]);
	const client = new SimplePythonClient(server);

	// 3. Use async iterator to manage lifecycle
	for await (const lsp of client.start()) {
		console.log("LSP Client is ready");

		const filePath = resolve("test.py");
		const uri = toURI(filePath);

		// 4. Open a virtual file
		await lsp.sync.didOpen(lsp, uri, "python", "import os\nprint(os.name)\n");

		// 5. Perform a request
		const hover = await lsp.hover.getHover(lsp, uri, 1, 8); // hover over 'os.name'
		console.log("Hover result:", JSON.stringify(hover, null, 2));
	}
}

run().catch(console.error);
