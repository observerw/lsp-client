import {
  type ClientCapabilities,
  type Hover
} from 'vscode-languageserver-protocol';
import type { LSPFeature, LSPClient } from '../client/abc';

export class HoverFeature implements LSPFeature {
  public fillClientCapabilities(caps: ClientCapabilities): void {
    caps.textDocument = caps.textDocument || {};
    caps.textDocument.hover = {
      contentFormat: ['markdown', 'plaintext'],
    };
  }

  public async getHover(client: LSPClient, uri: string, line: number, character: number): Promise<Hover | null> {
    return await client.sendRequest('textDocument/hover', {
      textDocument: { uri },
      position: { line, character },
    });
  }
}
