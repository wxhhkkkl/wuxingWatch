import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const push = vi.fn()
const back = vi.fn()
const replace = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push, back, replace }),
  useRoute: () => ({ params: { id: '1' } }),
}))

vi.mock('element-plus', async (importOriginal) => {
  const mod = await importOriginal<typeof import('element-plus')>()
  return {
    ...mod,
    ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
    ElMessageBox: { confirm: vi.fn(() => Promise.resolve()) },
  }
})

vi.mock('../src/api/adminBooks', () => ({
  listBooks: vi.fn(),
  deleteBook: vi.fn(),
  listCategories: vi.fn(),
  getBook: vi.fn(),
  createBook: vi.fn(),
  updateBook: vi.fn(),
  publishBook: vi.fn(),
  unpublishBook: vi.fn(),
  listChapters: vi.fn(),
  createChapter: vi.fn(),
  updateChapter: vi.fn(),
  deleteChapter: vi.fn(),
  reorderChapters: vi.fn(),
}))

import AdminBooks from '../src/pages/AdminBooks.vue'
import AdminBookEdit from '../src/pages/AdminBookEdit.vue'
import {
  createChapter,
  deleteBook,
  getBook,
  listBooks,
  listCategories,
  listChapters,
  updateBook,
} from '../src/api/adminBooks'

const flush = () => new Promise((r) => setTimeout(r))

const mkBook = (over: Record<string, unknown> = {}) => ({
  id: 1,
  title: '子平真诠',
  author: null,
  description: null,
  cover_url: null,
  category_id: 1,
  status: 'draft',
  chapter_count: 0,
  created_at: null,
  ...over,
})

describe('AdminBooks', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    push.mockClear()
    back.mockClear()
    replace.mockClear()
    vi.mocked(listBooks).mockReset()
    vi.mocked(deleteBook).mockReset()
    vi.mocked(listCategories).mockReset()
    vi.mocked(listCategories).mockResolvedValue({ items: [{ id: 1, name: '命理', sort_order: 0 }] } as never)
  })

  it('renders book list with status tags', async () => {
    vi.mocked(listBooks).mockResolvedValue({
      items: [mkBook(), { ...mkBook(), id: 2, title: '滴天髓', status: 'published' }],
      total: 2,
      page: 1,
      page_size: 20,
    } as never)
    const wrapper = mount(AdminBooks)
    await flush()
    expect(wrapper.text()).toContain('子平真诠')
    expect(wrapper.text()).toContain('滴天髓')
    expect(wrapper.text()).toContain('已发布')
    expect(wrapper.text()).toContain('草稿')
  })

  it('navigates to edit on row action', async () => {
    vi.mocked(listBooks).mockResolvedValue({
      items: [mkBook()],
      total: 1,
      page: 1,
      page_size: 20,
    } as never)
    const wrapper = mount(AdminBooks)
    await flush()
    await wrapper
      .findAll('button')
      .find((b) => b.text() === '编辑')!
      .trigger('click')
    expect(push).toHaveBeenCalledWith('/books/1')
  })

  it('deletes a book after confirmation', async () => {
    vi.mocked(listBooks).mockResolvedValue({
      items: [mkBook()],
      total: 1,
      page: 1,
      page_size: 20,
    } as never)
    vi.mocked(deleteBook).mockResolvedValue(undefined)
    const wrapper = mount(AdminBooks)
    await flush()
    await wrapper
      .findAll('button')
      .find((b) => b.text() === '删除')!
      .trigger('click')
    await flush()
    expect(deleteBook).toHaveBeenCalledWith(1)
  })
})

describe('AdminBookEdit', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    push.mockClear()
    back.mockClear()
    replace.mockClear()
    vi.mocked(getBook).mockReset()
    vi.mocked(updateBook).mockReset()
    vi.mocked(listCategories).mockReset()
    vi.mocked(listCategories).mockResolvedValue({ items: [{ id: 1, name: '命理', sort_order: 0 }] } as never)
    vi.mocked(listChapters).mockReset()
    vi.mocked(listChapters).mockResolvedValue({ items: [] } as never)
    vi.mocked(createChapter).mockReset()
  })

  it('prefills the form from an existing book and saves', async () => {
    vi.mocked(getBook).mockResolvedValue(mkBook({ title: '滴天髓' }) as never)
    vi.mocked(updateBook).mockResolvedValue(mkBook() as never)
    const wrapper = mount(AdminBookEdit)
    await flush()
    const input = wrapper.find('input[placeholder="必填"]')
    expect((input.element as HTMLInputElement).value).toBe('滴天髓')
    await wrapper.find('button.el-button--primary').trigger('click')
    await flush()
    expect(updateBook).toHaveBeenCalledTimes(1)
    expect(replace).toHaveBeenCalledWith('/books')
  })

  it('creates a chapter from the book edit page', async () => {
    vi.mocked(getBook).mockResolvedValue(mkBook() as never)
    vi.mocked(createChapter).mockResolvedValue({
      id: 1,
      book_id: 1,
      title: '第一章',
      content: null,
      sort_order: 1,
    } as never)
    const wrapper = mount(AdminBookEdit)
    await flush()
    await wrapper
      .findAll('button')
      .find((b) => b.text() === '新增章节')!
      .trigger('click')
    await flush()
    const input = wrapper.find('.el-dialog input[placeholder="必填"]')
    await input.setValue('第一章')
    await wrapper
      .findAll('.el-dialog button')
      .find((b) => b.text() === '保存')!
      .trigger('click')
    await flush()
    expect(createChapter).toHaveBeenCalledWith(1, { title: '第一章', content: '' })
  })
})
