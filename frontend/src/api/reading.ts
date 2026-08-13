import { request } from './client'
import type { ReadingBook, ReadingBookList, ReadingCategory, ReadingChapterDetail } from '../types'

export function listReadingCategories(): Promise<{ items: ReadingCategory[] }> {
  return request('/api/reading/categories')
}

export function listReadingBooks(params: {
  page?: number
  page_size?: number
  category_id?: number
} = {}): Promise<ReadingBookList> {
  const q = new URLSearchParams()
  if (params.page) q.set('page', String(params.page))
  if (params.page_size) q.set('page_size', String(params.page_size))
  if (params.category_id !== undefined && params.category_id !== null) {
    q.set('category_id', String(params.category_id))
  }
  const s = q.toString()
  return request(`/api/reading/books${s ? `?${s}` : ''}`)
}

export function getReadingBook(id: number): Promise<ReadingBook> {
  return request(`/api/reading/books/${id}`)
}

export function getReadingChapter(
  bookId: number,
  chapterId: number,
): Promise<ReadingChapterDetail> {
  return request(`/api/reading/books/${bookId}/chapters/${chapterId}`)
}

export function updateReadingProgress(bookId: number, chapterId: number): Promise<void> {
  return request(`/api/reading/books/${bookId}/progress`, {
    method: 'PUT',
    body: JSON.stringify({ chapter_id: chapterId }),
  })
}
