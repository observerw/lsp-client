import { SafeLSPServer } from '../src/server/safe';
import { LSPClient, SyncFeature, toURI } from '../src';
import { resolve } from 'path';

class UsingTestClient extends LSPClient {
  public sync = new SyncFeature();

  constructor(server: SafeLSPServer) {
    super(server);
    this.registerFeature(this.sync);
  }

  protected getLanguageId() { return 'python'; }
  protected createInitializationOptions() { return {}; }
}

async function demonstrateUsingSyntax() {
  console.log('🧪 Demonstrating TypeScript `using` syntax with LSP\n');

  // Test 1: Basic using with automatic disposal
  console.log('1️⃣ Basic `using` syntax:');
  {
    using server = new SafeLSPServer(['pyrefly', 'lsp']);
    const connection = await server.start();
    console.log('   ✅ Server started, will auto-dispose when scope ends');
    await new Promise(r => setTimeout(r, 500));
  }
  console.log('   ✅ Server automatically disposed after scope end\n');

  // Test 2: Using with LSP client lifecycle
  console.log('2️⃣ LSP client with `using`:');
  {
    const lspServer = new SafeLSPServer(['pyrefly', 'lsp']);
    const testClient = new UsingTestClient(lspServer);

    // Using in the client lifecycle with disposable connection
    for await (const lsp of testClient.start()) {
      console.log('   ✅ LSP client started');
      
      const uri = toURI(resolve('test_using.py'));
      await lsp.sync.didOpen(lsp, uri, 'python', 'print("Hello from using syntax!")\n');
      
      // Client cleanup happens automatically when generator ends
      break;
    }
  }
  console.log('   ✅ LSP client and server disposed automatically\n');

  // Test 3: Error safety with disposable connection
  console.log('3️⃣ Error safety with `using`:');
  try {
    const errorServer = new SafeLSPServer(['pyrefly', 'lsp']);
    using disposableConnection = errorServer.getDisposableConnection();
    await disposableConnection.connection.listen();
    
    console.log('   ✅ Server started with disposable connection');
    throw new Error('Something went wrong!');
  } catch (error) {
    console.log(`   ✅ Error caught: ${error instanceof Error ? error.message : String(error)}`);
    console.log('   ✅ Server connection still disposed automatically');
  }
}

demonstrateUsingSyntax().catch(console.error);
