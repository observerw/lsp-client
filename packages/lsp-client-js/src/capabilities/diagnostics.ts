import { type PublishDiagnosticsParams } from 'vscode-languageserver-protocol'
import type { MessageConnection } from 'vscode-jsonrpc'
import type { LSPFeature, LSPClient } from '../client/abc'

export type DiagnosticsCallback = (params: PublishDiagnosticsParams) => void

export class DiagnosticsFeature implements LSPFeature {
  private callbacks: DiagnosticsCallback[] = []

  public onDiagnostics(callback: DiagnosticsCallback) {
    this.callbacks.push(callback)
  }

  public registerHandlers(_client: LSPClient, connection: MessageConnection): void {
    connection.onNotification(
      'textDocument/publishDiagnostics',
      (params: PublishDiagnosticsParams) => {
        for (const cb of this.callbacks) {
          cb(params)
        }
      },
    )
  }
}
