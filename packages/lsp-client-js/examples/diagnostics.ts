import { LocalServer, LSPClient, SyncFeature, DiagnosticsFeature, toURI } from '../src'
import { resolve } from 'path'

class DiagnosticClient extends LSPClient {
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
    return {}
  }
}

async function run() {
  const server = new LocalServer(['pyright-langserver', '--stdio'])
  const client = new DiagnosticClient(server)

  // Register callback BEFORE starting to ensure we don't miss early notifications
  client.diagnostics.onDiagnostics((params) => {
    console.log(`\n[Diagnostics] Received for ${params.uri}:`)
    params.diagnostics.forEach((d) => {
      console.log(` - [${d.severity}] ${d.message} (line ${d.range.start.line})`)
    })
  })

  for await (const lsp of client.start()) {
    const uri = toURI(resolve('error.py'))

    console.log('Opening file with intentional error...')
    await lsp.sync.didOpen(lsp, uri, 'python', 'import non_existent_module\n')

    // Wait for diagnostics to arrive (they are pushed by the server)
    console.log('Waiting for diagnostics...')
    await new Promise((r) => setTimeout(r, 3000))
  }
}

run().catch(console.error)
