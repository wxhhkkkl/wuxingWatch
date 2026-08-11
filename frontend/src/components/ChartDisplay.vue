<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { ChartResult } from '../types'
import { wxColor } from '../utils/wuxing'
import { defaultDayunIndex, defaultLiunianYear } from '../utils/selection'
import PillarTable from './PillarTable.vue'
import FortuneStrip from './FortuneStrip.vue'

const props = defineProps<{ result: ChartResult }>()

const router = useRouter()

const xi = computed(() => props.result.xi_yong)

// 大运/流年联动选中态（默认跟随当前日期）
const currentYear = new Date().getFullYear()
const steps = computed(() => props.result.da_yun.steps)
const hasYears = computed(() => steps.value.some((s) => s.start_year != null))
const selectedDayunIndex = ref(defaultDayunIndex(props.result.da_yun.steps, currentYear))
const selectedLiunianYear = ref<number | null>(null)

const selectedStep = computed(() => steps.value[selectedDayunIndex.value] ?? null)
const selectedLiunian = computed(
  () => selectedStep.value?.liu_nian?.find((n) => n.year === selectedLiunianYear.value) ?? null,
)

watch(
  selectedDayunIndex,
  (i) => {
    const s = steps.value[i]
    selectedLiunianYear.value = s ? defaultLiunianYear(s, currentYear) : null
  },
  { immediate: true },
)

const birthYear = computed(() =>
  props.result.solar_birth ? new Date(props.result.solar_birth).getFullYear() : null,
)

function fmtDateTime(s: string): string {
  const d = new Date(s)
  if (isNaN(d.getTime())) return s
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${p(d.getHours())}:${p(d.getMinutes())}`
}
</script>

<template>
  <div class="chart">
    <p v-if="result.note" class="note-banner">{{ result.note }}</p>
    <div v-if="result.dst?.in_dst" class="dst-banner">
      夏令时提示：{{ result.dst.note }}<br />
      原时间 {{ fmtDateTime(result.dst.original_time) }} → 修正为 {{ fmtDateTime(result.dst.corrected_time) }}
    </div>

    <!-- 出生信息 -->
    <section class="wx-card">
      <p class="wx-card-title">出生信息</p>
      <template v-if="result.solar_birth">
        <div class="info-row"><span>公历</span>{{ fmtDateTime(result.solar_birth) }}</div>
        <div class="info-row"><span>农历</span>{{ result.lunar_birth }}</div>
        <div
          class="info-row"
          data-testid="row-true-solar"
          :class="{ 'is-link': result.shichen?.applied }"
          @click="result.shichen?.applied && router.push('/shichen')"
        >
          <span>真太阳时</span>{{ fmtDateTime(result.true_solar_time) }}
          <small v-if="result.shichen?.applied" class="muted">查看时辰详解 ›</small>
        </div>
        <div class="info-row"><span>地区</span>{{ result.birth_place || '—' }}</div>
        <div v-if="result.shichen?.applied && result.shichen.shichen" class="info-row">
          <span>精确时辰</span>
          {{ result.shichen.shichen }}时
          <small class="muted">传统均分法：{{ result.shichen.traditional_shichen }}时</small>
        </div>
        <div v-if="result.jieqi" class="info-line">
          <span>出生节气</span>出生于{{ result.jieqi.prev.name }}后<b>{{ result.jieqi.prev.days }}</b>天<b>{{ result.jieqi.prev.hours }}</b>小时，{{ result.jieqi.next.name }}前<b>{{ result.jieqi.next.days }}</b>天<b>{{ result.jieqi.next.hours }}</b>小时
        </div>
        <div v-if="result.jieqi" class="two-col">
          <div><span>{{ result.jieqi.prev.name }}</span>{{ fmtDateTime(result.jieqi.prev.time) }}</div>
          <div><span>{{ result.jieqi.next.name }}</span>{{ fmtDateTime(result.jieqi.next.time) }}</div>
        </div>
        <div v-if="result.xing_zuo" class="two-col">
          <div><span>星座</span>{{ result.xing_zuo }}</div>
          <div v-if="result.xing_xiu"><span>星宿</span>{{ result.xing_xiu }}</div>
        </div>
      </template>
      <template v-else>
        <div class="info-row"><span>方式</span>四柱输入</div>
        <div class="info-row">
          <span>四柱</span>
          {{ result.pillars.year?.ganzhi }} {{ result.pillars.month?.ganzhi }}
          {{ result.pillars.day?.ganzhi }} {{ result.pillars.time?.ganzhi }}
        </div>
        <div class="info-row"><span>地区</span>{{ result.birth_place || '—' }}</div>
      </template>
    </section>

    <!-- 四柱明细（流年/大运列随横条选中联动） -->
    <section class="wx-card">
      <p class="wx-card-title">四柱 · 日主 {{ result.day_master }}</p>
      <PillarTable
        :pillars="result.pillars"
        :selected-dayun="hasYears ? selectedStep : null"
        :selected-liunian="hasYears ? selectedLiunian : null"
      />
      <p v-if="result.missing_parts.length" class="warn">时辰不详：无法排出时柱、命宫、身宫。</p>
    </section>

    <!-- 大运 · 流年联动 -->
    <section class="wx-card">
      <p class="wx-card-title">大运 · 流年</p>
      <FortuneStrip
        :steps="steps"
        :selected-dayun-index="selectedDayunIndex"
        :selected-liunian-year="selectedLiunianYear"
        :start-age="result.da_yun.start_age"
        :start-month="result.da_yun.start_month"
        :birth-year="birthYear"
        @select-dayun="selectedDayunIndex = $event"
        @select-liunian="selectedLiunianYear = $event"
      />
    </section>

    <!-- 人元司令与宫位 -->
    <section class="wx-card">
      <p class="wx-card-title">人元司令 · 胎元 · 宫位</p>
      <div class="info-row">
        <span>人元司令</span>
        藏干 {{ result.hidden_stems.hidden_stems.join('、') }} · 当令 {{ result.hidden_stems.ruling_stem }}
      </div>
      <div class="info-row"><span>胎元</span>{{ result.tai_yuan }}</div>
      <div class="info-row"><span>命宫</span>{{ result.ming_gong ?? '—' }}</div>
      <div class="info-row"><span>身宫</span>{{ result.shen_gong ?? '—' }}</div>
      <p class="muted">{{ result.hidden_stems.source }}</p>
    </section>

    <!-- 喜忌分析 -->
    <section class="wx-card">
      <p class="wx-card-title">喜忌分析 · {{ xi.conclusion.summary }}</p>
      <div class="xi-summary">
        <div class="xi-item">
          <span class="xi-label">用神</span>
          <span class="xi-value" :style="{ color: wxColor(xi.conclusion.yong_shen) }">
            {{ xi.conclusion.yong_shen }}
          </span>
        </div>
        <div class="xi-item">
          <span class="xi-label">喜神</span>
          <span class="xi-value">{{ xi.conclusion.xi_shen.join('、') || '—' }}</span>
        </div>
        <div class="xi-item">
          <span class="xi-label">忌神</span>
          <span class="xi-value avoid">{{ xi.conclusion.ji_shen.join('、') || '—' }}</span>
        </div>
      </div>
      <p class="xi-line">
        宜用五行：<b>{{ xi.favorable_elements.join('、') }}</b>
        <span class="muted"> · 忌用：{{ xi.avoid_elements.join('、') || '—' }}</span>
      </p>
      <p class="muted">{{ xi.reasoning }}</p>
      <p class="muted">
        事业：{{ xi.direction.career as string }}；财运：{{ xi.direction.fortune as string }}
      </p>
      <p class="disclaimer">{{ xi.disclaimer }}</p>
    </section>
  </div>
</template>

<style scoped>
.chart {
  padding-bottom: 12px;
}
.note-banner {
  background: #fdf3e0;
  border: 1px solid #ecd9a8;
  color: #8a6d1a;
  border-radius: 10px;
  padding: 10px 12px;
  margin: 12px 14px;
  font-size: 13px;
}
.dst-banner {
  background: #e8f2fb;
  border: 1px solid #bcd8ee;
  color: #2d5f8a;
  border-radius: 10px;
  padding: 10px 12px;
  margin: 12px 14px;
  font-size: 13px;
  line-height: 1.6;
}
.info-row {
  display: flex;
  gap: 8px;
  font-size: 14px;
  padding: 3px 0;
}
.info-row span {
  color: var(--wx-muted);
  flex: 0 0 68px;
}
.info-row.is-link {
  cursor: pointer;
  color: var(--wx-primary-2, #a63431);
}
/* 出生节气整行句式 + 两列对齐行 */
.info-line {
  font-size: 14px;
  padding: 3px 0;
  line-height: 1.6;
}
.info-line span {
  color: var(--wx-muted);
  margin-right: 8px;
}
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  font-size: 14px;
  padding: 3px 0;
}
.two-col span {
  color: var(--wx-muted);
  margin-right: 6px;
}

/* 喜忌 */
.xi-summary {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
}
.xi-item {
  flex: 1;
  background: #faf6ee;
  border-radius: 10px;
  text-align: center;
  padding: 8px 4px;
}
.xi-label {
  display: block;
  font-size: 11px;
  color: var(--wx-muted);
}
.xi-value {
  font-size: 20px;
  font-weight: 600;
}
.xi-value.avoid {
  color: var(--wx-primary-2);
}
.xi-line {
  font-size: 14px;
  margin: 6px 0;
}
.muted {
  color: var(--wx-muted);
  font-size: 13px;
}
.warn {
  color: #b8860b;
  font-size: 13px;
  margin-top: 8px;
}
.disclaimer {
  color: var(--wx-muted);
  font-size: 12px;
  margin-top: 8px;
  border-top: 1px dashed var(--wx-line);
  padding-top: 8px;
}
</style>
