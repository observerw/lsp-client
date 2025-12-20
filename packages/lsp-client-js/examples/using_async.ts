import { SafeLSPServer } from '../src/server/safe';
import { LSPClient, SyncFeature, DiagnosticsFeature, toURI } from '../src';
import { resolve } from 'path';

class FileProcessingClient extends LSPClient {
  public sync = new SyncFeature();
  public diagnostics = new DiagnosticsFeature();

  constructor(server: SafeLSPServer) {
    super(server);
    this.registerFeature(this.sync);
    this.registerFeature(this.diagnostics);
  }

  protected getLanguageId() { return 'python'; }
  protected createInitializationOptions() { return {}; }
}

class TempFile implements Disposable {
  constructor(public path: string) {
    console.log(`📁 Creating temp file: ${this.path}`);
  }

  [Symbol.dispose]() {
    console.log(`🗑️  Disposing temp file: ${this.path}`);
    // In a real implementation, you'd delete the file here
  }
}

async function processFile() {
  console.log('🧪 Processing file with multiple `using` declarations\n');

  // Stack multiple disposals
  using tempFile = new TempFile('/tmp/test.txt');
  const server = new SafeLSPServer(['pyrefly', 'lsp']);
  const client = new FileProcessingClient(server);

  // Monitor diagnostics
  client.diagnostics.onDiagnostics((params) => {
    console.log(`🔍 Diagnostics for ${params.uri.split('/').pop()}: ${params.diagnostics.length} issues`);
  });

  console.log('📋 Starting LSP client...');
  
  // Use `await using` for async disposal with disposable connection
  using disposableConnection = server.getDisposableConnection();
  await disposableConnection.connection.listen();

  const uri = toURI(resolve('temp_analysis.py'));
  await client.sync.didOpen(client, uri, 'python', `
def process_data(items: list[str]) -> int:
    """Process some data and return count."""
    return len(items)

# Example usage
count = process_data(["a", "b", "c"])
print(f"Count: {count}")

# Type error example
bad_count = process_data([1, 2, 3])  # Numbers instead of strings
    `.trim());

  console.log('⏳ Analyzing file...');
  await new Promise(r => setTimeout(r, 2000));

  console.log('✅ Processing complete - all resources will be disposed automatically');
}

processFile().catch(console.error);
