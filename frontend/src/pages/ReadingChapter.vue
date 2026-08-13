<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
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

// 字号：小/中/大，持久化到本地
const FONT_KEYS = ['小', '中', '大'] as const
type FontKey = (typeof FONT_KEYS)[number]
const FONT_SIZE: Record<FontKey, number> = { 小: 14, 中: 16, 大: 18 }
const fontKey = ref<FontKey>(
  FONT_KEYS.includes(localStorage.getItem('reading_font') as FontKey)
    ? (localStorage.getItem('reading_font') as FontKey)
    : '中',
)
const fontSize = computed(() => FONT_SIZE[fontKey.value])

function setFont(k: FontKey) {
  fontKey.value = k
  localStorage.setItem('reading_font', k)
}

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
    <van-nav-bar
      fixed
      placeholder
      :title="chapter?.title ?? '阅读'"
      left-text="返回"
      left-arrow
      @click-left="router.back()"
    />

    <div class="reader">
      <!-- 字号调节 -->
      <div class="font-bar">
        <button
          v-for="k in FONT_KEYS"
          :key="k"
          class="font-btn"
          :class="{ active: fontKey === k }"
          @click="setFont(k)"
        >
          {{ k }}
        </button>
      </div>

      <div class="chapter-body">
        <h1 v-if="chapter" class="chapter-title">{{ chapter.title }}</h1>
        <div
          v-if="chapter"
          class="md-content"
          :style="{ '--fs': fontSize + 'px' }"
          v-html="renderMarkdown(chapter.content)"
        />
        <van-loading v-else-if="loading" class="chapter-loading" />
      </div>

      <div v-if="chapter" class="chapter-nav">
        <button
          class="nav-btn"
          :disabled="!chapter.prev_chapter_id"
          @click="go(chapter.prev_chapter_id!)"
        >
          上一章
        </button>
        <button
          class="nav-btn next"
          :disabled="!chapter.next_chapter_id"
          @click="go(chapter.next_chapter_id!)"
        >
          下一章
        </button>
      </div>
      <p v-if="chapter && !chapter.prev_chapter_id" class="edge-hint">已是第一章</p>
      <p v-if="chapter && !chapter.next_chapter_id" class="edge-hint">已是最后一章</p>
    </div>
  </div>
</template>

<style scoped>
.reading-page {
  min-height: 100vh;
  background: #fbf9f4;
}
.reader {
  max-width: 640px;
  margin: 0 auto;
  padding: 8px 0 24px;
}

/* 字号调节栏：滚动时粘在固定导航栏（46px）下方，不遮挡头部 */
.font-bar {
  position: sticky;
  top: 46px;
  z-index: 5;
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  padding: 8px 20px;
  background: rgba(251, 249, 244, 0.92);
}
.font-btn {
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 999px;
  padding: 2px 12px;
  font-size: 12px;
  color: #888;
}
.font-btn.active {
  border-color: #a63431;
  color: #a63431;
}

.chapter-body {
  padding: 12px 20px 8px;
}
.chapter-title {
  margin: 0 0 18px;
  font-size: 21px;
  line-height: 1.5;
  color: #2b2b2b;
  text-align: center;
}

/* 正文排版：纸感 + 首行缩进 + 舒适行距 */
.md-content {
  font-family: "PingFang SC", "Noto Serif SC", "Source Han Serif SC", "Songti SC", "SimSun",
    serif;
  font-size: var(--fs, 16px);
  line-height: 2;
  color: #333;
  word-break: break-word;
  letter-spacing: 0.02em;
}
.md-content :deep(p) {
  text-indent: 2em;
  margin: 0.55em 0;
}
.md-content :deep(h1),
.md-content :deep(h2),
.md-content :deep(h3) {
  text-indent: 0;
  margin: 1.2em 0 0.6em;
  font-weight: 600;
  color: #2b2b2b;
  line-height: 1.5;
}
.md-content :deep(h1) {
  font-size: 1.35em;
}
.md-content :deep(h2) {
  font-size: 1.2em;
}
.md-content :deep(h3) {
  font-size: 1.1em;
}
.md-content :deep(strong) {
  color: #2b2b2b;
}
.md-content :deep(blockquote) {
  margin: 0.8em 0;
  padding: 0.2em 0 0.2em 1em;
  border-left: 3px solid #e0c9b8;
  color: #666;
}
.md-content :deep(ul),
.md-content :deep(ol) {
  padding-left: 2em;
  margin: 0.6em 0;
}
.md-content :deep(img) {
  max-width: 100%;
  border-radius: 6px;
  margin: 0.8em 0;
}
.md-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.8em 0;
  font-size: 0.95em;
}
.md-content :deep(td),
.md-content :deep(th) {
  border: 1px solid #e5e0d6;
  padding: 6px 8px;
}

.chapter-loading {
  margin: 40px auto;
}

/* 章节导航 */
.chapter-nav {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding: 20px 0 8px;
}
.nav-btn {
  flex: 1;
  max-width: 160px;
  border: 1px solid #d8cfc2;
  background: #fff;
  color: #555;
  border-radius: 999px;
  padding: 10px 0;
  font-size: 15px;
}
.nav-btn.next {
  border-color: #a63431;
  color: #fff;
  background: #a63431;
}
.nav-btn:disabled {
  opacity: 0.35;
}
.edge-hint {
  text-align: center;
  color: #999;
  font-size: 12px;
  margin: 6px 0 16px;
}
</style>
