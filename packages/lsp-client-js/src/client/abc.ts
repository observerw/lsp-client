import { LSPServer } from '../server/abc';
import type { 
  ClientCapabilities, 
  InitializeParams, 
  InitializeResult,
  InitializeRequest,
  InitializedNotification,
} from 'vscode-languageserver-protocol';
import { 
  RequestType,
  NotificationType,
  type MessageConnection 
} from 'vscode-jsonrpc';
import { toURI } from '../utils/uri';
import { resolve } from 'path';

export interface LSPFeature {
  fillClientCapabilities?(caps: ClientCapabilities): void;
  initialize?(client: LSPClient, result: InitializeResult): void;
  registerHandlers?(client: LSPClient, connection: MessageConnection): void;
}

export abstract class LSPClient {
  protected server: LSPServer;
  public features: LSPFeature[] = [];
  protected workspaceRoot: string;

  constructor(server: LSPServer, workspaceRoot: string = process.cwd()) {
    this.server = server;
    this.workspaceRoot = resolve(workspaceRoot);
  }

  public registerFeature(feature: LSPFeature) {
    this.features.push(feature);
  }

  protected abstract getLanguageId(): string;
  protected abstract createInitializationOptions(): any;

  public async request<P, R, E>(type: RequestType<P, R, E>, params: P): Promise<R> {
    return await this.server.getConnection().sendRequest(type, params);
  }

  public async sendRequest(method: string, params: any): Promise<any> {
    return await this.server.getConnection().sendRequest(method, params);
  }

  public async notify<P>(type: NotificationType<P>, params: P): Promise<void> {
    await this.server.getConnection().sendNotification(type, params);
  }

  public async sendNotification(method: string, params: any): Promise<void> {
    await this.server.getConnection().sendNotification(method, params);
  }


  public async *start(): AsyncIterableIterator<this> {
    const caps: ClientCapabilities = {};
    for (const feature of this.features) {
      feature.fillClientCapabilities?.(caps);
    }

  // Using `using` for automatic connection disposal
  const connection = await this.server.start();

    // Register handlers from features
    for (const feature of this.features) {
      feature.registerHandlers?.(this, connection);
    }

    const rootUri = toURI(this.workspaceRoot);
    const initParams: InitializeParams = {
      processId: process.pid,
      capabilities: caps,
      initializationOptions: this.createInitializationOptions(),
      rootUri: rootUri,
      workspaceFolders: [
        {
          uri: rootUri,
          name: 'root'
        }
      ],
    };

    const initResult = await connection.sendRequest('initialize', initParams) as InitializeResult;
    await connection.sendNotification('initialized', {});

    for (const feature of this.features) {
      feature.initialize?.(this, initResult);
    }

    try {
      yield this;
    } finally {
      try {
        await connection.sendRequest('shutdown', null);
        await connection.sendNotification('exit', null);
      } catch (e) {
        // Ignore errors during shutdown
      }
      // Connection will be automatically disposed by `using` syntax
      await this.server.kill();
    }
  }
}
