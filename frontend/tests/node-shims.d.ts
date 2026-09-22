/**
 * 本仓库的 tsconfig 未引 node 类型（`types: ["vitest/globals", "vite/client"]`），
 * 而 `tests/style-sanity.spec.ts` 需要读 `.css` 源文件的正文——Vitest 会把 `.css` 的
 * **任何** import 形式（`?raw`/`?inline`/裸导入）截成空串，故只能落到 node 的 `fs`。
 *
 * 这里只声明本仓库用到的那**一个**函数，不为一个测试引整套 `@types/node`。
 */
declare module 'node:fs' {
  export function readFileSync(path: string | URL, encoding: 'utf8'): string
}
