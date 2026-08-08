<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import { deleteRecord, listRecords } from '../api/records'
import type { RecordSummary } from '../types'

const router = useRouter()
const records = ref<RecordSummary[]>([])
const loading = ref(false)

onMounted(load)

async function load() {
  loading.value = true
  try {
    records.value = await listRecords()
  } catch (e) {
    showToast((e as Error).message)
  } finally {
    loading.value = false
  }
}

function relationLabel(r: string) {
  return ({ SELF: '本人', CHILD: '子女', PARENT: '父母', OTHER: '其他' } as Record<string, string>)[r] ?? r
}

async function onDelete(id: number) {
  try {
    await showConfirmDialog({ title: '删除记录', message: '确定删除这条排盘记录吗？' })
  } catch {
    return
  }
  try {
    await deleteRecord(id)
    records.value = records.value.filter((r) => r.id !== id)
    showToast('已删除')
  } catch (e) {
    showToast((e as Error).message)
  }
}
</script>

<template>
  <div class="records-page">
    <van-nav-bar title="我的记录" left-text="返回" @click-left="router.back()" />
    <van-empty v-if="!loading && records.length === 0" description="还没有保存的排盘记录">
      <van-button type="primary" @click="router.push('/')">去排盘</van-button>
    </van-empty>
    <van-list v-else :loading="loading" :finished="true" finished-text="没有更多了">
      <van-cell
        v-for="r in records"
        :key="r.id"
        :title="`${r.person_name ?? '未命名'}（${relationLabel(r.relationship)}）`"
        :label="`${r.birth_solar.slice(0, 10)} · 保存于 ${r.created_at.slice(0, 10)}`"
        is-link
        @click="router.push(`/records/${r.id}`)"
      >
        <template #value>
          <van-button size="mini" plain type="danger" @click.stop="onDelete(r.id)">删除</van-button>
        </template>
      </van-cell>
    </van-list>
  </div>
</template>

<style scoped>
.records-page {
  min-height: 100vh;
}
</style>
