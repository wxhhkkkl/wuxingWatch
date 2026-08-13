import { marked } from 'marked'
import DOMPurify from 'dompurify'

marked.setOptions({ gfm: true, breaks: true })

/** Markdown → 净化后的 HTML（章节内容为后台录入文本，须防 XSS）。 */
export function renderMarkdown(md: string | null | undefined): string {
  const html = marked.parse(md ?? '', { async: false }) as string
  return DOMPurify.sanitize(html)
}
