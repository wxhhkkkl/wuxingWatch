/**
 * 样式表的「注释残渣」守卫（2026-09-22 补）。
 *
 * **为什么需要**：CSS 注释里把「星号」与「斜杠」**挨着写**会**提前结束注释**，
 * 剩下半句被当成选择器，**紧随其后的那条规则整条被吞掉**。真实踩过一次：
 * 注释里写了三个系列名并用斜杠分隔，于是那三处每一处都成了注释终点，而
 * **紧接其后的 `.pillar-row { display: flex }`** 首当其冲——全部命盘的柱列
 * **塌成竖排一条线**。
 *
 * 最阴的是：`npx vitest run`（默认不加载 CSS）、`vue-tsc`、`vite build`
 * （能打包成功、不报错）**没有一道会红**——只有人眼看得出。故在此用真解析器
 * 把「选择器里混进了注释文字」变成断言。
 *
 * ⚠️ 本文件自己的注释同样不许出现那两个字面相邻的字符（TypeScript 与 CSS 同规矩，
 * 本站已两度踩）。下文需要举例时一律用「星号斜杠」这个词，不写出字符。
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import postcss from 'postcss'

// 文件清单用 Vite 的 glob 拿（`.vue` 的正文它也读得到）；**但 `.css` 的正文只能走 fs**
// ——Vitest 会把 `.css` 的任何 import 形式截成空串（`?raw`、`?inline`、裸导入都试过）。
const PATHS = Object.keys(import.meta.glob('../src/**/*.{css,vue}', { eager: true }))
const srcOf = (rel: string) => readFileSync(new URL(rel, import.meta.url), 'utf8')

/** 一个文件里的全部 CSS：`.css` 即全文；`.vue` 取各 `<style>` 块（**没有样式块就是空的**
 *  ——不能拿「有没有 `<style>`」当判据，那会把整个 `.vue` 正文当 CSS 去解析）。 */
function cssBlocks(rel: string, src: string): string[] {
  if (!rel.endsWith('.vue')) return [src]
  return [...src.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)].map((m) => m[1])
}

/** 注释残渣的指纹：选择器里出现**反引号或中文标点**。
 *
 *  只认这两样，**不认汉字**——汉字在 CSS 标识符里合法，本仓库就有正当用处
 *  （`RelationDiagram.vue` 的 `.rd-edge--冲`、`.rd-edge--三会` 等）。而漏出来的
 *  注释句子必然带反引号（写代码标识用的）或 `。）、` 这类标点，两样都不会出现在
 *  正常类名里。 */
const JUNK = /[`。，、：；？！（）「」『』×＋－]/

/** 注释里出现了「星号紧跟斜杠」——就是本文件守的那个错。 */
const STAR_SLASH = /\*\//

describe('样式表健全性', () => {
  it('选择器里不得混进注释文字（注释被星号斜杠提前结束的症状）', () => {
    const bad: string[] = []
    for (const rel of PATHS) {
      for (const css of cssBlocks(rel, srcOf(rel))) {
        // `postcss` 不会因残渣报错（它照样解析成一个畸形选择器），故判据是
        // 「选择器里有没有反引号/中文标点」这类只有注释才有的字符。
        postcss.parse(css, { from: rel }).walkRules((r) => {
          if (JUNK.test(r.selector)) {
            bad.push(`${rel}: ${JSON.stringify(r.selector.slice(0, 70))}`)
          }
        })
      }
    }
    expect(bad, '这些选择器里混进了注释残渣——去查对应注释里的星号斜杠').toEqual([])
  })

  it('共享样式表的关键规则都在（`display:flex` 不许被吞）', () => {
    // 上面那条的**正面**对照：真被吞过一次的就是这一条。
    const css = srcOf('../src/styles/chart.css')
    const ruleOf = (sel: string) => {
      let out: string | null = null
      postcss.parse(css, { from: 'chart.css' })
        .walkRules((r) => { if (r.selector === sel) out = r.toString() })
      return out
    }
    const row = ruleOf('.pillar-row')
    expect(row, 'chart.css 里应有 .pillar-row 规则').toBeTruthy()
    expect(row).toContain('display: flex')
    expect(ruleOf('.pillar-col')).toBeTruthy()
    expect(ruleOf('.step-chart')).toBeTruthy()
  })

  it('本文件的注释里也不含字面相邻的星号斜杠（写这条时又踩过一次）', () => {
    // 注释块的正常结尾当然含那两个字符，故先把它们去掉再查剩余。
    const withoutEnds = srcOf('./style-sanity.spec.ts')
      .replace(new RegExp(`[ \\t]*\\*${'/'}`, 'g'), '')
    expect(STAR_SLASH.test(withoutEnds), '本文件注释里混进了提前结束的星号斜杠').toBe(false)
  })
})
