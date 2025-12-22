import { type MessageConnection } from 'vscode-jsonrpc'

export class LSPServerConnection implements Disposable {
  private disposed = false

  constructor(public connection: MessageConnection) {}

  public getConnection(): MessageConnection {
    if (this.disposed) {
      throw new Error('Connection has been disposed')
    }
    return this.connection
  }

  [Symbol.dispose]() {
    if (!this.disposed) {
      this.connection.dispose()
      this.disposed = true
    }
  }
}
