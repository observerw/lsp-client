import { LSPServer, LSPServerConnection } from './abc';
import { 
  createMessageConnection, 
  StreamMessageReader, 
  StreamMessageWriter,
  type MessageConnection 
} from 'vscode-jsonrpc/node';
import { spawn, type ChildProcess } from 'node:child_process';

export class LocalServer extends LSPServer {
  private process: ChildProcess | null = null;
  private serverConnection?: LSPServerConnection;

  constructor(args: string[]) {
    super(args);
  }

  public override async start(): Promise<MessageConnection> {
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
    
    // Wrap connection with automatic disposal
    this.serverConnection = new LSPServerConnection(this.connection);
    return this.connection;
  }

  public override async kill(): Promise<void> {
    if (this.process) {
      this.process.kill();
      this.process = null;
    }
    if (this.connection) {
      this.connection.dispose();
      this.connection = undefined;
    }
    if (this.serverConnection) {
      this.serverConnection = undefined;
    }
  }
}