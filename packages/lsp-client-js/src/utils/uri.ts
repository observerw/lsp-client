import { pathToFileURL, fileURLToPath } from 'url';

export function toURI(path: string): string {
  return pathToFileURL(path).toString();
}

export function fromURI(uri: string): string {
  return fileURLToPath(uri);
}
