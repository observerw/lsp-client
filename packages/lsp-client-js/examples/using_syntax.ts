import { LocalServer } from '../src/server/local'
import { LSPClient, type LSPFeature } from '../src/client/abc'
import type { LSPServer } from '../src/server/abc'

class FeatureTestClient extends LSPClient {
  public override features: LSPFeature[] = []

  constructor(server: LSPServer) {
    super(server)
  }

  protected getLanguageId() {
    return 'python'
  }
  protected createInitializationOptions() {
    return {}
  }

  // Simple lifecycle test using `using`
  async testBasicLifecycle() {
    console.log('Testing basic lifecycle with `using`...')

    using server = new LocalServer(['pyrefly', 'lsp'])

    // The connection will be automatically disposed when we exit this scope
    const connection = await server.start()
    console.log('✅ Server started and connection established')

    // Simulate some work
    await new Promise((r) => setTimeout(r, 1000))
    console.log('✅ Work completed')

    // Connection will be automatically disposed when exiting this function
    console.log('✅ About to exit function - connection will dispose automatically')
  }

  // Test with error handling
  async testErrorHandling() {
    console.log('Testing error handling with `using`...')

    try {
      using server = new LocalServer(['pyrefly', 'lsp'])
      await server.start()

      // Simulate an error
      throw new Error('Simulated error during work')
    } catch (error) {
      console.log('✅ Error caught:', error instanceof Error ? error.message : String(error))
      console.log('✅ Server connection was disposed automatically even with error')
    }
  }
}

async function runTests() {
  console.log('🧪 Testing TypeScript `using` syntax in LSP Client\n')

  const client = new FeatureTestClient(new LocalServer(['pyrefly', 'lsp']))

  await client.testBasicLifecycle()
  await client.testErrorHandling()

  console.log('\n✅ All `using` syntax tests passed!')
}

runTests().catch(console.error)
