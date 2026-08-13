import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const push = vi.fn()
const back = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push, back }),
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

import ReadingBooks from '../src/pages/ReadingBooks.vue'
import { listReadingBooks, listReadingCategories } from '../src/api/reading'

const flush = () => new Promise((r) => setTimeout(r))

describe('ReadingBooks', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    push.mockClear()
    back.mockClear()
    vi.mocked(listReadingBooks).mockReset()
    vi.mocked(listReadingCategories).mockReset()
    vi.mocked(listReadingCategories).mockResolvedValue({ items: [] } as never)
  })

  it('renders only published books from the list', async () => {
    vi.mocked(listReadingBooks).mockResolvedValue({
      items: [
        { id: 1, title: '子平真诠', author: '沈孝瞻', description: null, cover_url: null, category_id: 1, chapter_count: 3 },
        { id: 2, title: '论语', author: null, description: null, cover_url: null, category_id: 2, chapter_count: 0 },
      ],
      total: 2,
      page: 1,
      page_size: 20,
    } as never)
    const wrapper = mount(ReadingBooks)
    await flush()
    expect(wrapper.text()).toContain('子平真诠')
    expect(wrapper.text()).toContain('论语')
  })

  it('navigates to book detail on click', async () => {
    vi.mocked(listReadingBooks).mockResolvedValue({
      items: [
        { id: 1, title: '子平真诠', author: null, description: null, cover_url: null, category_id: 1, chapter_count: 3 },
      ],
      total: 1,
      page: 1,
      page_size: 20,
    } as never)
    const wrapper = mount(ReadingBooks)
    await flush()
    await wrapper.find('.van-cell').trigger('click')
    expect(push).toHaveBeenCalledWith('/reading/books/1')
  })
})
