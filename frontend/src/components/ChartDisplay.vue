<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { ChartResult, LiuRiItem, LiuShiContext, LiuShiItem, LiuYueItem, V2Relation } from '../types'
import { fetchLiuShi, fetchSuiyun } from '../api/charts'
import { getRecordSuiyun } from '../api/records'
import { wxColor } from '../utils/wuxing'
import {
  defaultDayunIndex,
  defaultLiunianYear,
  defaultLiuriDate,
  defaultLiuyueBranch,
  shichenZhiOf,
} from '../utils/selection'
import PillarTable from './PillarTable.vue'
import FortuneStrip from './FortuneStrip.vue'
import RelationDiagram from './RelationDiagram.vue'
import { isWangduStrength, isWangduV2 } from '../types'
import { useChartStore } from '../stores/chart'

// `recordId` 由「记录详情」传入——不带它时 `/strength` 会去读**会话 store**，
// 从一条记录点进去就会串成上一次排盘的那张盘（或整页空）。
const props = defineProps<{ result: ChartResult; recordId?: number }>()

const router = useRouter()
const chartStore = useChartStore()

const xi = computed(() => props.result.xi_yong)

// 大运/流年联动选中态（默认跟随当前日期）
const currentYear = new Date().getFullYear()
const now = new Date()
const p2 = (n: number) => String(n).padStart(2, '0')
const todayStr = `${now.getFullYear()}-${p2(now.getMonth() + 1)}-${p2(now.getDate())}`
const steps = computed(() => props.result.da_yun.steps)
const hasYears = computed(() => steps.value.some((s) => s.start_year != null))
const selectedDayunIndex = ref(defaultDayunIndex(props.result.da_yun.steps, currentYear))
const selectedLiunianYear = ref<number | null>(null)

const selectedStep = computed(() => steps.value[selectedDayunIndex.value] ?? null)
const selectedLiunian = computed(
  () => selectedStep.value?.liu_nian?.find((n) => n.year === selectedLiunianYear.value) ?? null,
)

// 流月/流日/流时下钻：按需请求，逐级联动
const liuyueList = ref<LiuYueItem[]>([])
const selectedLiuyueBranch = ref<string | null>(null)
const liuriList = ref<LiuRiItem[]>([])
const selectedLiuriDate = ref<string | null>(null)
const liushiList = ref<LiuShiItem[]>([])
const selectedLiushiZhi = ref<string | null>(null)
const liuLoading = ref<'month' | 'day' | 'hour' | null>(null)

const liuContext = computed<LiuShiContext>(() => ({
  day_ganzhi: props.result.pillars.day?.ganzhi ?? '',
  year_ganzhi: props.result.pillars.year?.ganzhi ?? '',
  month_zhi: props.result.pillars.month?.zhi ?? '',
}))

const selectedLiuyue = computed(
  () => liuyueList.value.find((m) => m.branch === selectedLiuyueBranch.value) ?? null,
)
const selectedLiuri = computed(
  () => liuriList.value.find((d) => d.date === selectedLiuriDate.value) ?? null,
)
const selectedLiushi = computed(
  () => liushiList.value.find((h) => h.zhi === selectedLiushiZhi.value) ?? null,
)

// 四柱表下钻列（流月/流日/流时）显隐开关：默认显示，隐藏不影响横条联动
const showLiuCols = ref(true)
const hasLiuCols = computed(() => selectedLiuyue.value != null)

function resetCascade(level: 'month' | 'day' | 'hour') {
  if (level === 'month') {
    liuyueList.value = []
    selectedLiuyueBranch.value = null
  }
  if (level !== 'hour') {
    liuriList.value = []
    selectedLiuriDate.value = null
  }
  liushiList.value = []
  selectedLiushiZhi.value = null
}

// 各级自增 token：丢弃过期响应（快速连点时的竞态防护）
let monthToken = 0
let dayToken = 0
let hourToken = 0

watch(selectedLiunianYear, async (year) => {
  resetCascade('month')
  if (year == null || !hasYears.value) return
  const token = ++monthToken
  liuLoading.value = 'month'
  try {
    const res = await fetchLiuShi({ level: 'month', year, context: liuContext.value })
    if (token !== monthToken) return
    liuyueList.value = res.months
    if (year === currentYear) {
      const b = defaultLiuyueBranch(res.months, now)
      if (b) selectedLiuyueBranch.value = b
    }
  } catch {
    if (token === monthToken) liuyueList.value = []
  } finally {
    if (token === monthToken && liuLoading.value === 'month') liuLoading.value = null
  }
})

watch(selectedLiuyueBranch, async (branch) => {
  resetCascade('day')
  const year = selectedLiunianYear.value
  if (!branch || year == null) return
  const token = ++dayToken
  liuLoading.value = 'day'
  try {
    const res = await fetchLiuShi({ level: 'day', year, month_branch: branch, context: liuContext.value })
    if (token !== dayToken) return
    liuriList.value = res.days
    const t = defaultLiuriDate(res.days, now)
    if (t) selectedLiuriDate.value = t
  } catch {
    if (token === dayToken) liuriList.value = []
  } finally {
    if (token === dayToken && liuLoading.value === 'day') liuLoading.value = null
  }
})

watch(selectedLiuriDate, async (d) => {
  resetCascade('hour')
  const year = selectedLiunianYear.value
  const branch = selectedLiuyueBranch.value
  if (!d || year == null || !branch) return
  const token = ++hourToken
  liuLoading.value = 'hour'
  try {
    const res = await fetchLiuShi({ level: 'hour', year, month_branch: branch, date: d, context: liuContext.value })
    if (token !== hourToken) return
    liushiList.value = res.hours
    if (d === todayStr) selectedLiushiZhi.value = shichenZhiOf(now.getHours())
  } catch {
    if (token === hourToken) liushiList.value = []
  } finally {
    if (token === hourToken && liuLoading.value === 'hour') liuLoading.value = null
  }
})

watch(
  selectedDayunIndex,
  (i) => {
    const s = steps.value[i]
    selectedLiunianYear.value = s ? defaultLiunianYear(s, currentYear) : null
    chartStore.setViewingDayun(s?.ganzhi ?? null)  // 喜忌"大运介入"步联动（008）
  },
  { immediate: true },
)

const birthYear = computed(() =>
  props.result.solar_birth ? new Date(props.result.solar_birth).getFullYear() : null,
)

/** 进「加入大运」/「加入流年」页（013 FR-021a）——从记录进入时带上 id，
 *  使那两页按记录的输入**当场重推**岁运（岁运结论不落库，FR-026）。 */
function gotoStage(path: string) {
  router.push(props.recordId != null ? { path, query: { record: String(props.recordId) } } : path)
}

// ---- 阶段 3（加入流年）的后端关系裁定：命盘图的岁运维度**只消费后端产出**（013 T040）----
//
// 013 起流年的本地判定副本退役（方案 A）——否则同一命盘同一年份会在「加入流年」页
// 与命盘图上显示不同结论（违 FR-024 / SC-008）。取不到时传 null，命盘图退回
// 「该步大运」的后端裁定（仍非本地判定）。
const suiyun = ref<{
  ganzhi: string; year: number
  relations: { established: V2Relation[]; rejected: V2Relation[] }
} | null>(null)
let suiyunToken = 0

watch(
  [() => selectedStep.value?.ganzhi, selectedLiunianYear] as const,
  async ([gz, year]) => {
    suiyun.value = null                       // 换步 / 换年即失效，避免显示别年结论
    if (!hasYears.value || !gz || year == null) return
    if (!isWangduV2(xi.value.strength)) return // 非 v2：命盘图本就走本地兜底，无须请求
    const t = ++suiyunToken
    try {
      const res = props.recordId != null
        ? await getRecordSuiyun(props.recordId, gz, year)
        : chartStore.inputs
          ? await fetchSuiyun({ ...chartStore.inputs, dayun_ganzhi: gz, liunian_year: year })
          : null
      if (t !== suiyunToken || !res?.liunian) return
      suiyun.value = { ganzhi: gz, year, relations: res.liunian.relations }
    } catch {
      /* 取不到（未登录 / 无出生日期等）就退回该步大运的后端裁定 */
    }
  },
  { immediate: true },
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
      <p class="wx-card-title">
        四柱 · 日主 {{ result.day_master }}
        <label v-if="hasLiuCols" class="liu-toggle" data-testid="toggle-liu-cols">
          <input v-model="showLiuCols" type="checkbox" />
          流月/流日/流时
        </label>
      </p>
      <PillarTable
        :pillars="result.pillars"
        :selected-dayun="hasYears ? selectedStep : null"
        :selected-liunian="hasYears ? selectedLiunian : null"
        :selected-liuyue="showLiuCols ? selectedLiuyue : null"
        :selected-liuri="showLiuCols ? selectedLiuri : null"
        :selected-liushi="showLiuCols ? selectedLiushi : null"
      />
      <p v-if="result.missing_parts.length" class="warn">时辰不详：无法排出时柱、命宫、身宫。</p>
    </section>

    <!-- 命盘图（干支 · 流通 · 宫位 · 六亲；组件自带卡片与标题） -->
    <RelationDiagram
      :result="result"
      :selected-dayun="hasYears ? selectedStep : null"
      :selected-liunian="hasYears ? selectedLiunian : null"
      :suiyun="suiyun"
    />

    <!-- 大运 · 流年联动 -->
    <section class="wx-card">
      <p class="wx-card-title">大运 · 流年</p>
      <FortuneStrip
        :steps="steps"
        :selected-dayun-index="selectedDayunIndex"
        :selected-liunian-year="selectedLiunianYear"
        :start-age="result.da_yun.start_age"
        :start-month="result.da_yun.start_month"
        :start-day="result.da_yun.start_day"
        :start-hour="result.da_yun.start_hour"
        :jiao-yun="result.da_yun.jiao_yun"
        :birth-year="birthYear"
        :liuyue="liuyueList"
        :selected-liuyue-branch="selectedLiuyueBranch"
        :liuri="liuriList"
        :selected-liuri-date="selectedLiuriDate"
        :liushi="liushiList"
        :selected-liushi-zhi="selectedLiushiZhi"
        :loading-level="liuLoading"
        @select-dayun="selectedDayunIndex = $event"
        @select-liunian="selectedLiunianYear = $event"
        @select-liuyue="selectedLiuyueBranch = $event"
        @select-liuri="selectedLiuriDate = $event"
        @select-liushi="selectedLiushiZhi = $event"
      />
    </section>

    <!-- 岁运推导（013 三阶段）：原局 → 加入大运 → 加入流年，各成一页 -->
    <section class="wx-card">
      <p class="wx-card-title">岁运推导</p>
      <div class="stage-links">
        <span class="stage-link" data-testid="dayun-link" @click="gotoStage('/dayun')">
          加入大运<van-icon name="arrow" size="12" />
        </span>
        <span class="stage-link" data-testid="liunian-link" @click="gotoStage('/liunian')">
          加入流年<van-icon name="arrow" size="12" />
        </span>
      </div>
      <p class="muted">
        在原局之上逐步加入大运与流年重判；两阶段的同名判断并列罗列，引擎不合成吉凶。
      </p>
    </section>

    <!-- 人元司令与宫位 -->
    <section class="wx-card">
      <p class="wx-card-title">人元司令 · 胎元 · 宫位</p>
      <div class="info-row">
        <span>人元司令</span>
        藏干 {{ result.hidden_stems.hidden_stems.join('、') }} · 当令 {{ result.hidden_stems.ruling_stem }}
      </div>
      <div v-if="result.hidden_stems.wang_xiang" class="info-row" data-testid="row-wang-xiang">
        <span>旺相休囚死</span>
        <template v-for="s in ['旺', '相', '休', '囚', '死'] as const" :key="s">
          {{ s }}<b :style="{ color: wxColor(result.hidden_stems.wang_xiang![s]) }">{{
            result.hidden_stems.wang_xiang![s]
          }}</b>&nbsp;
        </template>
      </div>
      <div class="info-row"><span>胎元</span>{{ result.tai_yuan }}</div>
      <div class="info-row"><span>命宫</span>{{ result.ming_gong ?? '—' }}</div>
      <div class="info-row"><span>身宫</span>{{ result.shen_gong ?? '—' }}</div>
      <p class="muted">{{ result.hidden_stems.source }}</p>
    </section>

    <!-- 喜忌分析（008 旺度法：结论先行，双用神并列） -->
    <section class="wx-card">
      <p class="wx-card-title">
        喜忌分析
        <span
          v-if="isWangduStrength(xi.strength) || isWangduV2(xi.strength)"
          class="strength-link"
          data-testid="strength-link"
          @click="router.push(props.recordId != null
            ? { path: '/strength', query: { record: String(props.recordId) } }
            : '/strength')"
        >
          {{ xi.conclusion.summary }} · 查看计算过程<van-icon name="arrow" size="12" />
        </span>
        <span v-else-if="xi.strength" class="strength-fallback">
          · {{ xi.conclusion.summary }}（旧版口径，重新排盘可查看新法推演）
        </span>
        <span v-else class="strength-fallback"> · {{ xi.conclusion.summary }}</span>
      </p>
      <div class="xi-summary">
        <div class="xi-item">
          <span class="xi-label">用神</span>
          <span class="xi-value" :style="{ color: wxColor(xi.conclusion.yong_shen) }">
            {{ xi.conclusion.yong_shen }}
          </span>
        </div>
        <div v-if="xi.conclusion.tiaohou_yong_shen" class="xi-item">
          <span class="xi-label">调候</span>
          <span
            class="xi-value"
            :style="{ color: xi.conclusion.tiaohou_yong_shen.element ? wxColor(xi.conclusion.tiaohou_yong_shen.element) : undefined }"
          >
            {{ xi.conclusion.tiaohou_yong_shen.element ?? '不需调候' }}
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
/* 四柱卡片标题右侧的下钻列显隐开关 */
.wx-card-title {
  position: relative;
}
.liu-toggle {
  position: absolute;
  right: 0;
  top: 0;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 400;
  color: var(--wx-muted);
  cursor: pointer;
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
/* 喜忌区强弱标签（可点击进详情） */
.strength-link {
  margin-left: 6px;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  background: var(--wx-primary-2, #a63431);
  border-radius: 10px;
  padding: 1px 8px;
  cursor: pointer;
  vertical-align: middle;
}
.strength-fallback {
  font-size: 14px;
  font-weight: 600;
}
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
/* 岁运推导两个入口（013） */
.stage-links {
  display: flex;
  gap: 10px;
  margin: 6px 0;
}
.stage-link {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 13px;
  font-weight: 600;
  color: var(--wx-primary-2, #a63431);
  background: #fbf3f3;
  border-radius: 12px;
  padding: 4px 12px;
  cursor: pointer;
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
