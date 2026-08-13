<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { listReadingBooks, listReadingCategories } from '../api/reading'
import type { ReadingBookSummary, ReadingCategory } from '../types'

const router = useRouter()
const categories = ref<ReadingCategory[]>([])
const activeCat = ref<number | undefined>(undefined)
const items = ref<ReadingBookSummary[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const finished = ref(false)

async function load(reset = false) {
  if (reset) {
    page.value = 1
    finished.value = false
    items.value = []
  }
  loading.value = true
  try {
    const body = await listReadingBooks({
      page: page.value,
      page_size: pageSize,
      category_id: activeCat.value,
    })
    items.value = reset ? body.items : [...items.value, ...body.items]
    total.value = body.total
    if (items.value.length >= body.total) finished.value = true
    else page.value += 1
  } catch (e) {
    showToast((e as Error).message)
    finished.value = true
  } finally {
    loading.value = false
  }
}

function onCatChange(index: number) {
  activeCat.value = categories.value[index]?.id
  load(true)
}

onMounted(async () => {
  try {
    categories.value = (await listReadingCategories()).items
  } catch {
    /* 分类加载失败不阻塞列表 */
  }
  load(true)
})
</script>

<template>
  <div class="reading-page">
    <van-nav-bar title="阅读" />

    <van-tabs v-if="categories.length" @change="onCatChange">
      <van-tab title="全部" />
      <van-tab v-for="c in categories" :key="c.id" :title="c.name" />
    </van-tabs>

    <van-list v-model:loading="loading" :finished="finished" finished-text="没有更多了" @load="load()">
      <van-cell-group inset class="wx-card" style="margin-top: 8px">
        <van-cell
          v-for="b in items"
          :key="b.id"
          :title="b.title"
          :label="b.author ?? (b.chapter_count ? `${b.chapter_count} 章` : '')"
          is-link
          @click="router.push(`/reading/books/${b.id}`)"
        >
          <template #value>
            <van-tag plain type="primary">{{ b.chapter_count }} 章</van-tag>
          </template>
        </van-cell>
        <van-empty v-if="!loading && items.length === 0" description="暂无书籍" />
      </van-cell-group>
    </van-list>
  </div>
</template>
