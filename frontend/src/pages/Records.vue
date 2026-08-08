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
    <van-nav-bar title="我的记录" left-text="返回" left-arrow @click-left="router.back()" />

    <van-empty
      v-if="!loading && records.length === 0"
      description="还没有保存的排盘记录"
    >
      <van-button type="primary" round @click="router.push('/')">去排盘</van-button>
    </van-empty>

    <van-list v-else :loading="loading" :finished="true" finished-text="没有更多了">
      <div class="record-list">
        <van-swipe-cell v-for="r in records" :key="r.id">
          <div class="record-card" @click="router.push(`/records/${r.id}`)">
            <div class="record-avatar">
              {{ (r.person_name ?? '未')[0] }}
            </div>
            <div class="record-main">
              <div class="record-title">
                {{ r.person_name ?? '未命名' }}
                <span class="record-tag">{{ relationLabel(r.relationship) }}</span>
              </div>
              <div class="record-meta">
                公历 {{ r.birth_solar.slice(0, 10) }} · 保存于 {{ r.created_at.slice(0, 10) }}
              </div>
            </div>
            <van-icon name="arrow" color="#c9b892" />
          </div>
          <template #right>
            <van-button square type="danger" text="删除" class="delete-btn" @click="onDelete(r.id)" />
          </template>
        </van-swipe-cell>
      </div>
    </van-list>
  </div>
</template>

<style scoped>
.record-list {
  padding: 10px 14px;
}
.record-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  border-radius: 12px;
  padding: 12px 14px;
  margin-bottom: 10px;
  box-shadow: 0 1px 4px rgba(90, 60, 30, 0.06);
}
.record-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: linear-gradient(135deg, #a63431, #c25b4e);
  color: #fff;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.record-main {
  flex: 1;
  min-width: 0;
}
.record-title {
  font-size: 15px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}
.record-tag {
  font-size: 11px;
  color: #a63431;
  background: #f8ecea;
  border-radius: 8px;
  padding: 1px 6px;
}
.record-meta {
  font-size: 12px;
  color: var(--wx-muted);
  margin-top: 3px;
}
.delete-btn {
  height: 100%;
}
</style>
