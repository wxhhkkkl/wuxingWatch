<script setup lang="ts">
/** 015：大运逐步格局喜忌（格名以原局为基准，允许变格）。 */
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getRecord } from '../api/records'
import { fetchGeju, getRecordGeju } from '../api/geju'
import { useChartStore } from '../stores/chart'
import { GEJU_STATUS_LABEL, gejuName, strengthText } from '../utils/geju'
import type { ChartResult, GeJuResponse } from '../types'

const router = useRouter()
const route = useRoute()
const store = useChartStore()

const chart = ref<ChartResult | null>(null)
const resp = ref<GeJuResponse | null>(null)
const error = ref('')
const loading = ref(true)
const selected = ref(0)

const yuanju = computed(() => resp.value?.yuanju ?? null)
const steps = computed(() => resp.value?.dayun_steps ?? [])
const current = computed(() => steps.value[selected.value] ?? null)
const statusLabel = computed(() => {
  const s = yuanju.value?.status ?? 'undetermined'
  return GEJU_STATUS_LABEL[s] ?? s
})

onMounted(async () => {
  const rid = Number(route.query.record)
  try {
    if (rid) {
      const rec = await getRecord(rid)
      chart.value = rec.chart_result
      resp.value = await getRecordGeju(rid)
    } else {
      chart.value = store.result
      if (store.inputs) resp.value = await fetchGeju({ ...store.inputs })
    }
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="detail-page">
    <van-nav-bar title="格局喜忌 · 大运" left-text="返回" left-arrow @click-left="router.back()" />

    <van-loading v-if="loading" class="loading" />
    <p v-else-if="error" class="warn-line">{{ error }}</p>
    <van-empty v-else-if="!steps.length" description="该盘暂无可用的格局大运步" />

    <template v-else>
      <section class="wx-card">
        <p class="wx-card-title">选择大运</p>
        <div class="step-row">
          <button
            v-for="(s, i) in steps"
            :key="s.ganzhi"
            class="step-btn"
            :class="{ active: i === selected }"
            :data-testid="`geju-step-${s.ganzhi}`"
            @click="selected = i"
          >{{ s.ganzhi }}</button>
        </div>
        <p class="muted">原局格名：{{ gejuName(yuanju?.main_ge ?? null) }}（{{ statusLabel }}）</p>
      </section>

      <template v-if="current">
        <section class="wx-card" data-testid="geju-dayun-verdict">
          <p class="wx-card-title">{{ current.ganzhi }} · 判定</p>
          <p class="ge-name">{{ gejuName(current.ge) }}</p>
          <p class="ge-meta">
            <span>{{ strengthText(current.shen_qiang_ruo) }}</span>
            <span v-if="current.change.type" class="change">{{ current.change.type }}</span>
          </p>
          <p v-if="current.change.reason" class="muted">{{ current.change.reason }}</p>
          <p class="muted">
            差异：身强弱 {{ current.diff.strength }}；喜忌 {{ current.diff.xi_ji }}；
            成破 {{ current.diff.cheng_po }}；格 {{ current.diff.ge }}
          </p>
        </section>

        <section class="wx-card">
          <p class="wx-card-title">行运喜忌</p>
          <p class="muted">喜：{{ current.yun_xi_ji.xi.join('、') || '—' }}</p>
          <p class="muted">忌：{{ current.yun_xi_ji.ji.join('、') || '—' }}</p>
        </section>

        <section v-if="current.open_issues.length" class="wx-card">
          <p class="wx-card-title">存疑 / 未定</p>
          <ul class="issues">
            <li v-for="o in current.open_issues" :key="o.id">
              {{ o.texts.map((t) => t.text).join('；') }}
            </li>
          </ul>
        </section>
      </template>
    </template>
  </div>
</template>

<style scoped>
.step-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0; }
.step-btn {
  border: 1px solid var(--wx-line, #ddd);
  background: #fff;
  border-radius: 14px;
  padding: 4px 12px;
  font-size: 13px;
  cursor: pointer;
}
.step-btn.active { color: #fff; background: var(--wx-primary-2, #a63431); border-color: var(--wx-primary-2, #a63431); }
.ge-name { margin: 2px 0 6px; font-size: 20px; font-weight: 600; }
.ge-meta { display: flex; flex-wrap: wrap; gap: 8px; font-size: 13px; margin: 0 0 6px; }
.change { color: var(--wx-primary-2, #a63431); font-weight: 600; }
.muted { font-size: 12px; color: var(--wx-muted, #888); margin: 4px 0; }
.warn-line { color: #a15c00; font-size: 12px; }
.issues { margin: 6px 0 0; padding-left: 18px; font-size: 13px; }
</style>
