<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { getReadingChapter, updateReadingProgress } from '../api/reading'
import { renderMarkdown } from '../utils/markdown'
import type { ReadingChapterDetail } from '../types'

const route = useRoute()
const router = useRouter()
const bookId = Number(route.params.bookId)
const chapter = ref<ReadingChapterDetail | null>(null)
const loading = ref(false)

async function load() {
  const chapterId = Number(route.params.chapterId)
  loading.value = true
  try {
    chapter.value = await getReadingChapter(bookId, chapterId)
    // 记住上次章节（FR-010a），失败不阻断阅读
    updateReadingProgress(bookId, chapterId).catch(() => {})
  } catch (e) {
    showToast((e as Error).message)
    router.back()
  } finally {
    loading.value = false
  }
}

function go(id: number) {
  router.replace(`/reading/books/${bookId}/chapters/${id}`)
}

watch(() => route.params.chapterId, load)

onMounted(load)
</script>

<template>
  <div class="reading-page">
    <van-nav-bar :title="chapter?.title ?? '阅读'" left-text="返回" left-arrow @click-left="router.back()" />

    <div class="chapter-body">
      <div v-if="chapter" class="md-content" v-html="renderMarkdown(chapter.content)" />
      <van-loading v-else-if="loading" class="chapter-loading" />
    </div>

    <div v-if="chapter" class="chapter-nav">
      <van-button
        round
        size="small"
        plain
        :disabled="!chapter.prev_chapter_id"
        @click="go(chapter.prev_chapter_id!)"
      >
        上一章
      </van-button>
      <van-button
        round
        size="small"
        plain
        type="primary"
        :disabled="!chapter.next_chapter_id"
        @click="go(chapter.next_chapter_id!)"
      >
        下一章
      </van-button>
    </div>
    <p v-if="chapter && !chapter.prev_chapter_id" class="edge-hint">已是第一章</p>
    <p v-if="chapter && !chapter.next_chapter_id" class="edge-hint">已是最后一章</p>
  </div>
</template>

<style scoped>
.chapter-body {
  padding: 16px 20px 8px;
}
.md-content {
  font-size: 15px;
  line-height: 1.85;
  word-break: break-word;
}
.chapter-loading {
  margin: 40px auto;
}
.chapter-nav {
  display: flex;
  justify-content: center;
  gap: 24px;
  padding: 16px 0 4px;
}
.edge-hint {
  text-align: center;
  color: #999;
  font-size: 12px;
  margin: 4px 0 16px;
}
</style>
