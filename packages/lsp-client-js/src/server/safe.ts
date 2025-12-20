import { 
  createMessageConnection, 
  StreamMessageReader, 
  StreamMessageWriter,
  type MessageConnection 
} from 'vscode-jsonrpc/node';
import { spawn, type ChildProcess } from 'node:child_process';
import { LSPServer } from './abc';

export class DisposableConnection implements Disposable {
  constructor(public connection: MessageConnection, private process: ChildProcess) {}

  [Symbol.dispose]() {
    this.connection.dispose();
    this.process.kill();
  }
}

export class SafeLSPServer extends LSPServer {
  private process: ChildProcess | null = null;
  private connection: MessageConnection | null = null;

  constructor(args: string[]) {
    super(args);
  }

  public async start(): Promise<MessageConnection> {
    const [command, ...args] = this.args;
    this.process = spawn(command!, args, {
      stdio: ['pipe', 'pipe', 'inherit'],
    });

    if (!this.process.stdout || !this.process.stdin) {
      throw new Error('Failed to open stdout or stdin');
    }

    const reader = new StreamMessageReader(this.process.stdout);
    const writer = new StreamMessageWriter(this.process.stdin);

    this.connection = createMessageConnection(reader, writer);
    this.connection.listen();
    return this.connection;
  }

  public override getConnection(): MessageConnection {
    if (!this.connection) {
      throw new Error('Server not started');
    }
    return this.connection;
  }

  public override async kill(): Promise<void> {
    if (this.process) {
      this.process.kill();
      this.process = null;
    }
    if (this.connection) {
      this.connection.dispose();
      this.connection = null;
    }
  }

  // Return a disposable wrapper for the connection
  public getDisposableConnection(): DisposableConnection {
    if (!this.connection || !this.process) {
      throw new Error('Server not started');
    }
    return new DisposableConnection(this.connection, this.process);
  }
}