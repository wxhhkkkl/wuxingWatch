import { request } from './client'

export interface AdminCategory {
  id: number
  name: string
  sort_order: number
}

export interface AdminBook {
  id: number
  title: string
  author: string | null
  description: string | null
  cover_url: string | null
  category_id: number | null
  status: 'draft' | 'published'
  chapter_count: number
  created_at: string | null
}

export interface BookInput {
  title: string
  author?: string | null
  description?: string | null
  cover_url?: string | null
  category_id?: number | null
}

export interface AdminChapter {
  id: number
  book_id: number
  title: string
  content: string | null
  sort_order: number
}

export interface BookListPage {
  items: AdminBook[]
  total: number
  page: number
  page_size: number
}

// ---------- 分类 ----------

export function listCategories(): Promise<{ items: AdminCategory[] }> {
  return request('/api/admin/categories')
}

export function createCategory(data: { name: string; sort_order: number }): Promise<AdminCategory> {
  return request('/api/admin/categories', { method: 'POST', body: JSON.stringify(data) })
}

export function updateCategory(
  id: number,
  data: { name: string; sort_order: number },
): Promise<AdminCategory> {
  return request(`/api/admin/categories/${id}`, { method: 'PUT', body: JSON.stringify(data) })
}

export function deleteCategory(id: number): Promise<void> {
  return request(`/api/admin/categories/${id}`, { method: 'DELETE' })
}

// ---------- 书籍 ----------

export function listBooks(params: {
  page?: number
  page_size?: number
  keyword?: string
  category_id?: number
} = {}): Promise<BookListPage> {
  const q = new URLSearchParams()
  if (params.page) q.set('page', String(params.page))
  if (params.page_size) q.set('page_size', String(params.page_size))
  if (params.keyword) q.set('keyword', params.keyword)
  if (params.category_id !== undefined && params.category_id !== null) {
    q.set('category_id', String(params.category_id))
  }
  const s = q.toString()
  return request(`/api/admin/books${s ? `?${s}` : ''}`)
}

export function getBook(id: number): Promise<AdminBook> {
  return request(`/api/admin/books/${id}`)
}

export function createBook(data: BookInput): Promise<AdminBook> {
  return request('/api/admin/books', { method: 'POST', body: JSON.stringify(data) })
}

export function updateBook(id: number, data: BookInput): Promise<AdminBook> {
  return request(`/api/admin/books/${id}`, { method: 'PUT', body: JSON.stringify(data) })
}

export function deleteBook(id: number): Promise<void> {
  return request(`/api/admin/books/${id}`, { method: 'DELETE' })
}

export function publishBook(id: number): Promise<AdminBook> {
  return request(`/api/admin/books/${id}/publish`, { method: 'POST' })
}

export function unpublishBook(id: number): Promise<AdminBook> {
  return request(`/api/admin/books/${id}/unpublish`, { method: 'POST' })
}

// ---------- 章节 ----------

export function listChapters(bookId: number): Promise<{ items: AdminChapter[] }> {
  return request(`/api/admin/books/${bookId}/chapters`)
}

export function createChapter(
  bookId: number,
  data: { title: string; content?: string | null },
): Promise<AdminChapter> {
  return request(`/api/admin/books/${bookId}/chapters`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateChapter(
  bookId: number,
  chapterId: number,
  data: { title: string; content?: string | null },
): Promise<AdminChapter> {
  return request(`/api/admin/books/${bookId}/chapters/${chapterId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export function deleteChapter(bookId: number, chapterId: number): Promise<void> {
  return request(`/api/admin/books/${bookId}/chapters/${chapterId}`, { method: 'DELETE' })
}

export function reorderChapters(bookId: number, chapterIds: number[]): Promise<void> {
  return request(`/api/admin/books/${bookId}/chapters/reorder`, {
    method: 'PUT',
    body: JSON.stringify({ chapter_ids: chapterIds }),
  })
}
