import { LocalServer, LSPClient, SyncFeature, DiagnosticsFeature, toURI } from '../src'
import { resolve } from 'path'

class SimplePyreflyClient extends LSPClient {
  public sync = new SyncFeature()
  public diagnostics = new DiagnosticsFeature()

  constructor(server: LocalServer) {
    super(server)
    this.registerFeature(this.sync)
    this.registerFeature(this.diagnostics)
  }

  protected getLanguageId() {
    return 'python'
  }

  protected createInitializationOptions() {
    return {
      trace: { server: 'verbose' }, // Enable verbose logging
      diagnostic_mode: 'OpenFilesOnly', // Try different diagnostic mode
    }
  }
}

async function testDiagnostics() {
  console.log('Testing Pyrefly Diagnostics...')

  const server = new LocalServer(['pyrefly', 'lsp'])
  const client = new SimplePyreflyClient(server)

  let diagnosticCount = 0

  client.diagnostics.onDiagnostics((params) => {
    diagnosticCount++
    console.log(`\n[Diagnostic #${diagnosticCount}] ${params.uri}`)
    console.log(`Found ${params.diagnostics.length} issues:`)

    params.diagnostics.forEach((d, i) => {
      const severity =
        d.severity === 1
          ? 'ERROR'
          : d.severity === 2
            ? 'WARNING'
            : d.severity === 3
              ? 'INFO'
              : 'HINT'
      console.log(`  ${i + 1}. [${severity}] Line ${d.range.start.line + 1}: ${d.message}`)
    })
  })

  for await (const lsp of client.start()) {
    console.log('Pyrefly LSP Client connected!')

    const uri = toURI(resolve('error_test.py'))

    console.log('\nOpening file with intentional type error...')
    await lsp.sync.didOpen(
      lsp,
      uri,
      'python',
      `
def add_numbers(a: int, b: int) -> int:
    return a + b

# This should work fine
result1 = add_numbers(5, 10)
print(f"Result 1: {result1}")

# This will have a type error - strings instead of ints
result2 = add_numbers("hello", "world")
print(f"Result 2: {result2}")
    `.trim(),
    )

    console.log('Waiting for diagnostics...')

    // Wait longer for comprehensive analysis
    await new Promise((r) => setTimeout(r, 5000))

    console.log(`\nTotal diagnostic batches received: ${diagnosticCount}`)

    if (diagnosticCount === 0) {
      console.log('No diagnostics received. This might indicate:')
      console.log('1. Pyrefly is not detecting the errors')
      console.log('2. Diagnostic mode settings need adjustment')
      console.log('3. File may not be in the correct workspace')
    }
  }
}

testDiagnostics().catch(console.error)
