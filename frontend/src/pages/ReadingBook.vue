<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { getReadingBook } from '../api/reading'
import type { ReadingBook } from '../types'

const route = useRoute()
const router = useRouter()
const bookId = Number(route.params.id)
const book = ref<ReadingBook | null>(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    book.value = await getReadingBook(bookId)
  } catch (e) {
    showToast((e as Error).message)
    router.back()
  } finally {
    loading.value = false
  }
}

function openChapter(chapterId: number) {
  router.push(`/reading/books/${bookId}/chapters/${chapterId}`)
}

function resume() {
  const id = book.value?.current_chapter_id ?? book.value?.chapters[0]?.id
  if (id) openChapter(id)
}

onMounted(load)
</script>

<template>
  <div class="reading-page">
    <van-nav-bar title="书籍详情" left-text="返回" left-arrow @click-left="router.back()" />

    <div class="book-head">
      <h2 class="title">{{ book?.title }}</h2>
      <p v-if="book?.author" class="author">{{ book.author }}</p>
      <p v-if="book?.description" class="desc">{{ book.description }}</p>
      <van-button
        v-if="book?.chapters.length"
        type="primary"
        round
        size="small"
        class="resume-btn"
        @click="resume"
      >
        {{ book.current_chapter_id ? '继续阅读' : '开始阅读' }}
      </van-button>
    </div>

    <van-cell-group inset class="wx-card" style="margin-top: 8px">
      <van-cell
        v-for="c in book?.chapters ?? []"
        :key="c.id"
        :title="c.title"
        :label="`第 ${c.sort_order} 章`"
        is-link
        @click="openChapter(c.id)"
      />
      <van-empty v-if="book && !loading && book.chapters.length === 0" description="暂无章节" />
    </van-cell-group>
  </div>
</template>

<style scoped>
.book-head {
  padding: 20px 20px 8px;
}
.title {
  margin: 0;
  font-size: 20px;
}
.author {
  margin: 6px 0 0;
  color: #888;
  font-size: 13px;
}
.desc {
  margin: 8px 0 0;
  color: #666;
  font-size: 13px;
  line-height: 1.6;
}
.resume-btn {
  margin-top: 12px;
}
</style>
