import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const push = vi.fn()
const back = vi.fn()
const replace = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push, back, replace }),
  useRoute: () => ({ params: { bookId: '1', chapterId: '2' } }),
}))

vi.mock('vant', () => ({
  showToast: vi.fn(),
  showSuccessToast: vi.fn(),
}))

vi.mock('../src/api/reading', () => ({
  listReadingBooks: vi.fn(),
  listReadingCategories: vi.fn(),
  getReadingBook: vi.fn(),
  getReadingChapter: vi.fn(),
  updateReadingProgress: vi.fn(),
}))

import ReadingChapter from '../src/pages/ReadingChapter.vue'
import { getReadingChapter, updateReadingProgress } from '../src/api/reading'

const flush = () => new Promise((r) => setTimeout(r))

describe('ReadingChapter', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    push.mockClear()
    back.mockClear()
    replace.mockClear()
    vi.mocked(getReadingChapter).mockReset()
    vi.mocked(updateReadingProgress).mockReset()
    vi.mocked(updateReadingProgress).mockResolvedValue(undefined)
  })

  it('renders chapter content and reports progress', async () => {
    vi.mocked(getReadingChapter).mockResolvedValue({
      id: 2,
      book_id: 1,
      title: '第二章',
      content: '# 标题\n\n正文内容',
      prev_chapter_id: 1,
      next_chapter_id: 3,
    } as never)
    const wrapper = mount(ReadingChapter)
    await flush()
    expect(wrapper.text()).toContain('第二章')
    expect(wrapper.text()).toContain('正文内容')
    expect(updateReadingProgress).toHaveBeenCalledWith(1, 2)
    expect(wrapper.find('button').text()).toBe('上一章')
  })

  it('navigates to next chapter via replace', async () => {
    vi.mocked(getReadingChapter).mockResolvedValue({
      id: 2,
      book_id: 1,
      title: '第二章',
      content: '正文',
      prev_chapter_id: 1,
      next_chapter_id: 3,
    } as never)
    const wrapper = mount(ReadingChapter)
    await flush()
    const buttons = wrapper.findAll('button')
    const nextBtn = buttons.find((b) => b.text() === '下一章')
    await nextBtn!.trigger('click')
    expect(replace).toHaveBeenCalledWith('/reading/books/1/chapters/3')
  })
})
