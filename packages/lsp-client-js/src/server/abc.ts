import type { MessageConnection } from 'vscode-jsonrpc';

export abstract class LSPServer {
  protected args: string[];
  protected connection?: MessageConnection;

  public abstract start(): Promise<MessageConnection>;
  public abstract kill(): Promise<void>;

  public get isRunning(): boolean {
    return this.connection !== undefined;
  }

  public getConnection(): MessageConnection {
    if (!this.connection) {
      throw new Error('Server not started');
    }
    return this.connection;
  }
}

export class LSPServerConnection implements Disposable {
  private disposed = false;

  constructor(public connection: MessageConnection) {}

  public getConnection(): MessageConnection {
    if (this.disposed) {
      throw new Error('Connection has been disposed');
    }
    return this.connection;
  }

  [Symbol.dispose]() {
    if (!this.disposed) {
      this.connection.dispose();
      this.disposed = true;
    }
  }
}
