<script setup lang="ts">
/** 015：原局格局喜忌详情（正官格垂直切片起步）。 */
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getRecord } from '../api/records'
import { fetchGeju, getRecordGeju } from '../api/geju'
import { useChartStore } from '../stores/chart'
import PillarBoard from '../components/PillarBoard.vue'
import { natalColumns } from '../utils/chartColumns'
import { GEJU_STATUS_LABEL, gejuName, strengthText } from '../utils/geju'
import type { ChartResult, GeJuResponse, GeJuYongShen } from '../types'

const router = useRouter()
const route = useRoute()
const store = useChartStore()

const chart = ref<ChartResult | null>(null)
const resp = ref<GeJuResponse | null>(null)
const error = ref('')
const loading = ref(true)

const columns = computed(() => (chart.value ? natalColumns(chart.value.pillars) : []))
const ge = computed(() => resp.value?.yuanju.main_ge ?? null)
function yongText(y: GeJuYongShen): string {
  return `${y.element}（${y.book_term}）`
}

const statusLabel = computed(() =>
  resp.value ? (GEJU_STATUS_LABEL[resp.value.yuanju.status] ?? resp.value.yuanju.status) : '')

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
    <van-nav-bar title="格局喜忌 · 原局" left-text="返回" left-arrow @click-left="router.back()" />

    <van-loading v-if="loading" class="loading" />
    <p v-else-if="error" class="warn-line">{{ error }}</p>
    <van-empty v-else-if="!resp" description="暂无格局结果，请重新排盘" />

    <template v-else>
      <section v-if="columns.length" class="wx-card">
        <p class="wx-card-title">命盘</p>
        <PillarBoard :columns="columns" />
      </section>

      <section class="wx-card" data-testid="geju-verdict">
        <p class="wx-card-title">判定</p>
        <p class="ge-name" data-testid="geju-main">{{ gejuName(ge) }}</p>
        <p class="ge-meta">
          <span class="badge">{{ statusLabel }}</span>
          <span>{{ strengthText(resp.yuanju.shen_qiang_ruo) }}</span>
          <span>{{ resp.yuanju.gao_di.value }}</span>
        </p>
        <p v-if="resp.yuanju.concurrent_ge.length" class="muted">
          兼格：{{ resp.yuanju.concurrent_ge.map((g) => gejuName(g)).join(' / ') }}
        </p>
        <p v-if="resp.yuanju.main_ge_basis" class="muted">
          取格依据：{{ resp.yuanju.main_ge_basis.text }}
          （{{ resp.yuanju.main_ge_basis.citation.chapter }} {{ resp.yuanju.main_ge_basis.citation.section }} ·
          {{ resp.yuanju.main_ge_basis.citation.page }}）
        </p>
        <p v-for="(d, i) in resp.yuanju.degradations" :key="i" class="warn-line">⚠️ {{ d }}</p>
      </section>

      <section class="wx-card" data-testid="geju-chengpo">
        <p class="wx-card-title">成破 · 病药 · 高低</p>
        <p class="yong-line">状态：{{ statusLabel }} · 层次 {{ resp.yuanju.gao_di.value }}</p>
        <p v-if="resp.yuanju.disease.length" class="muted">
          病：{{ resp.yuanju.disease.map((d) => d.text).join('；') }}
        </p>
        <p v-if="resp.yuanju.remedy" class="muted">
          药：{{ resp.yuanju.remedy.path }}（{{ resp.yuanju.remedy.result }}）
        </p>
        <p class="muted">{{ resp.yuanju.gao_di.reasons.join('；') }}</p>
      </section>

      <section v-if="resp.yuanju.yong_shen" class="wx-card" data-testid="geju-yongxi">
        <p class="wx-card-title">用神 · 相神 · 喜忌</p>
        <p class="yong-line">用神：{{ yongText(resp.yuanju.yong_shen) }}<span class="muted"> · {{ resp.yuanju.yong_shen.role }}</span></p>
        <p class="muted">相神：{{ resp.yuanju.xiang_shen.map(yongText).join(' / ') || '—' }}</p>
        <p class="muted">喜神：{{ resp.yuanju.xi_shen.map(yongText).join('、') || '—' }}</p>
        <p class="muted">忌神：{{ resp.yuanju.ji_shen.map(yongText).join('、') || '—' }}</p>
        <p class="muted">{{ resp.yuanju.yong_shen.reason }}</p>
      </section>

      <section class="wx-card" data-testid="geju-conditions">
        <p class="wx-card-title">逐条条件</p>
        <table class="cond-table">
          <thead><tr><th>条件</th><th>结果</th><th>书证</th></tr></thead>
          <tbody>
            <tr v-for="c in resp.yuanju.conditions" :key="c.id" :data-testid="`cond-${c.id}`">
              <td>{{ c.text }}</td>
              <td :class="c.result ? 'ok' : 'no'">{{ c.result ? '✓' : '✗' }}{{ c.branch ? ` · ${c.branch}` : '' }}</td>
              <td class="cite">{{ c.citation.chapter }} {{ c.citation.section }}<br />{{ c.citation.page }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section v-if="resp.yuanju.open_issues.length" class="wx-card" data-testid="geju-open-issues">
        <p class="wx-card-title">存疑 / 未定</p>
        <p class="muted">以下条件书中未定或尚未编码，引擎不选边：</p>
        <ul class="issues">
          <li v-for="o in resp.yuanju.open_issues" :key="o.id">
            {{ o.texts.map((t) => t.text).join('；') }}
            <small>（{{ o.location.chapter }} {{ o.location.section }} · {{ o.location.page }}）</small>
          </li>
        </ul>
      </section>
    </template>
  </div>
</template>

<style scoped>
.ge-name { margin: 2px 0 6px; font-size: 20px; font-weight: 600; }
.yong-line { margin: 0 0 4px; font-size: 14px; font-weight: 600; }
.ge-meta { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 0 0 6px; font-size: 13px; }
.badge { border-radius: 10px; padding: 1px 8px; font-size: 12px; color: #fff; background: var(--wx-primary-2, #a63431); }
.muted { font-size: 12px; color: var(--wx-muted, #888); margin: 4px 0; }
.warn-line { color: #a15c00; font-size: 12px; }
.cond-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.cond-table th, .cond-table td { padding: 6px 4px; border-bottom: 1px solid var(--wx-line, #eee); text-align: left; vertical-align: top; }
.cond-table .ok { color: #2e7d32; }
.cond-table .no { color: #a63431; }
.cite { color: var(--wx-muted, #888); white-space: nowrap; }
.issues { margin: 6px 0 0; padding-left: 18px; font-size: 13px; }
.issues li { margin-bottom: 4px; }
</style>
