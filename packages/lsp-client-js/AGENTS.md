# AGENTS.md

Default to using Bun instead of Node.js.

- Use `bun <file>` instead of `node <file>` or `ts-node <file>`
- Use `bun test` instead of `jest` or `vitest`
- Use `bun build <file.html|file.ts|file.css>` instead of `webpack` or `esbuild`
- Use `bun install` instead of `npm install` or `yarn install` or `pnpm install`
- Use `bun run <script>` instead of `npm run <script>` or `yarn run <script>` or `pnpm run <script>`
- Use `bunx <package> <command>` instead of `npx <package> <command>`
- Bun automatically loads .env, so don't use dotenv.

## Development Commands

- Lint: `bun run lint`
- Fix linting issues: `bun run lint:fix`
- Format code: `bun run format`
- Type checking: `bun run typecheck`
- Run tests: `bun test`

## Code Style Guidelines

- Runtime: Bun
- Lint & Format: Biome
- Types: Full type annotations required
- Style: Follow existing patterns in `src/`. Use functional patterns where appropriate.

## APIs

- `Bun.serve()` supports WebSockets, HTTPS, and routes. Don't use `express`.
- `bun:sqlite` for SQLite. Don't use `better-sqlite3`.
- `Bun.redis` for Redis. Don't use `ioredis`.
- `Bun.sql` for Postgres. Don't use `pg` or `postgres.js`.
- `WebSocket` is built-in. Don't use `ws`.
- Prefer `Bun.file` over `node:fs`'s readFile/writeFile
- Bun.$`ls` instead of execa.

## Project Structure

- `src/`: Core implementation
  - `capabilities/`: LSP capability implementations (hover, definition, etc.)
  - `client/`: Base client classes
  - `server/`: Server connection handling (local, safe)
  - `utils/`: Common utilities (URI handling, etc.)
- `examples/`: Usage examples

```ts#index.test.ts
import { test, expect } from "bun:test";

test("hello world", () => {
  expect(1).toBe(1);
});
```
