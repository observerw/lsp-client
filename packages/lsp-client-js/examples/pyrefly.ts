import {
	LocalServer,
	LSPClient,
	SyncFeature,
	HoverFeature,
	DefinitionFeature,
	DiagnosticsFeature,
	toURI,
} from "../src";
import { resolve } from "path";

class PyreflyClient extends LSPClient {
	public sync = new SyncFeature();
	public hover = new HoverFeature();
	public definition = new DefinitionFeature();
	public diagnostics = new DiagnosticsFeature();

	constructor(server: LocalServer) {
		super(server);
		this.registerFeature(this.sync);
		this.registerFeature(this.hover);
		this.registerFeature(this.definition);
		this.registerFeature(this.diagnostics);
	}

	protected getLanguageId() {
		return "python";
	}

	protected createInitializationOptions() {
		return {
			trace: { server: "off" },
			diagnostic_mode: "Workspace",
		};
	}
}

async function testPyrefly() {
	console.log("Testing Pyrefly LSP Client...");

	const server = new LocalServer(["pyrefly", "lsp"]);
	const client = new PyreflyClient(server);

	// Set up diagnostics listener
	client.diagnostics.onDiagnostics((params) => {
		console.log(
			`\n[Pyrefly Diagnostics] ${params.diagnostics.length} issues found:`,
		);
		params.diagnostics.forEach((d) => {
			console.log(
				` - [${d.severity}] Line ${d.range.start.line + 1}: ${d.message}`,
			);
		});
	});

	for await (const lsp of client.start()) {
		console.log("Pyrefly LSP Client connected successfully!");

		// Test 1: Open a simple Python file
		const testFile = resolve("test_pyrefly.py");
		const uri = toURI(testFile);

		console.log(`\nOpening file: ${testFile}`);
		await lsp.sync.didOpen(
			lsp,
			uri,
			"python",
			`
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

result = greet("World")
print(result)

# This will have a type error
bad_result = greet(123)
    `.trim(),
		);

		// Test 2: Hover request
		console.log("\nTesting hover on function signature...");
		try {
			const hover = await lsp.hover.getHover(lsp, uri, 1, 8); // hover on "greet("
			console.log("Hover result:", JSON.stringify(hover, null, 2));
		} catch (e) {
			console.log(
				"Hover request failed:",
				e instanceof Error ? e.message : String(e),
			);
		}

		// Test 3: Definition request
		console.log("\nTesting definition on function call...");
		try {
			const def = await lsp.definition.getDefinition(lsp, uri, 5, 10); // definition of "greet" in call
			console.log("Definition result:", JSON.stringify(def, null, 2));
		} catch (e) {
			console.log(
				"Definition request failed:",
				e instanceof Error ? e.message : String(e),
			);
		}

		// Wait for diagnostics
		console.log("\nWaiting for diagnostics...");
		await new Promise((r) => setTimeout(r, 3000));

		console.log("\nTest completed successfully!");
	}
}

testPyrefly().catch(console.error);
