<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { ChartResult, Dayun2Step, LiuRiItem, LiuShiContext, LiuShiItem, LiuYueItem } from '../types'
import { fetchDayun2, fetchLiuShi } from '../api/charts'
import { getRecordDayun2 } from '../api/records'
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
import { useChartStore } from '../stores/chart'

// `recordId` 由「记录详情」传入——不带它时 `/strength` 会去读**会话 store**，
// 从一条记录点进去就会串成上一次排盘的那张盘（或整页空）。
const props = defineProps<{ result: ChartResult; recordId?: number }>()

const router = useRouter()
const chartStore = useChartStore()

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
  },
  { immediate: true },
)

const birthYear = computed(() =>
  props.result.solar_birth ? new Date(props.result.solar_birth).getFullYear() : null,
)

// ---- 原局旺度 / 当前大运旺度（引擎2）----
const WUXING = ['木', '火', '土', '金', '水'] as const
const wanDu = computed(() => props.result.wan_du)
const wanDuRows = computed(() =>
  WUXING.map((wx) => ({ wx, value: wanDu.value?.final_scores[wx] ?? 0 })),
)

/** 当前大运：按当前日期定位（不随横条选择变化——横条只驱动流年展示）。 */
const currentDayunIndex = computed(() => defaultDayunIndex(steps.value, currentYear))
const currentDayunStep = computed(() => steps.value[currentDayunIndex.value] ?? null)

const dayun2Steps = ref<Dayun2Step[]>([])
const dayun2Error = ref('')
const dayun2Current = computed(() =>
  dayun2Steps.value.find((s) => s.ganzhi === currentDayunStep.value?.ganzhi) ?? null,
)
const dayun2Rows = computed(() =>
  WUXING.map((wx) => ({ wx, value: dayun2Current.value?.elements[wx]?.dynamic ?? 0 })),
)

onMounted(async () => {
  if (!currentDayunStep.value) return
  try {
    const resp = props.recordId != null
      ? await getRecordDayun2(props.recordId)
      : chartStore.inputs
        ? await fetchDayun2({ ...chartStore.inputs })
        : null
    dayun2Steps.value = resp?.dayun_steps ?? []
  } catch (e) {
    dayun2Error.value = (e as Error).message
  }
})

/** 进详情页——从记录进入时带上 id，使详情页按记录的输入重推。 */
function gotoDetail(path: string) {
  router.push(props.recordId != null ? { path, query: { record: String(props.recordId) } } : path)
}

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

    <!-- 原局动态旺度 -->
    <section class="wx-card" data-testid="wan-du-card">
      <p class="wx-card-title">
        原局动态旺度
        <span v-if="wanDu" class="strength-link" data-testid="strength-link" @click="gotoDetail('/strength')">
          查看计算过程<van-icon name="arrow" size="12" />
        </span>
      </p>
      <div class="step-scores">
        <div v-for="r in wanDuRows" :key="r.wx" class="score-cell" :data-wx="r.wx">
          <span class="score-wx step-score-wx" :style="{ color: wxColor(r.wx) }">{{ r.wx }}</span>
          <span class="score-val">{{ r.value }}</span>
        </div>
      </div>
      <p v-if="wanDu" class="muted">
        日主 {{ wanDu.day_master }}（{{ wanDu.day_master_wuxing }}）· 动态
        {{ wanDu.final_scores[wanDu.day_master_wuxing] }} 度 · {{ wanDu.level }}
      </p>
    </section>

    <!-- 当前大运动态旺度（引擎2） -->
    <section class="wx-card" data-testid="dayun2-wandu-card">
      <p class="wx-card-title">
        大运动态旺度<template v-if="currentDayunStep"> · {{ currentDayunStep.ganzhi }}</template>
        <span v-if="currentDayunStep" class="strength-link" data-testid="dayun2-link" @click="gotoDetail('/dayun2')">
          查看计算过程<van-icon name="arrow" size="12" />
        </span>
      </p>
      <template v-if="dayun2Current">
        <div class="step-scores">
          <div v-for="r in dayun2Rows" :key="r.wx" class="score-cell" :data-wx="r.wx">
            <span class="score-wx step-score-wx" :style="{ color: wxColor(r.wx) }">{{ r.wx }}</span>
            <span class="score-val">{{ r.value }}</span>
          </div>
        </div>
        <p class="muted">
          日主 {{ dayun2Current.day_master.stem }}（{{ dayun2Current.day_master.wx }}）· 动态
          {{ dayun2Current.day_master.dynamic }} 度 · {{ dayun2Current.day_master.level }}
        </p>
      </template>
      <p v-else class="muted">{{ dayun2Error || '大运旺度暂无数据' }}</p>
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

/* 旺度卡片的「查看计算过程」入口 */
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
.muted {
  color: var(--wx-muted);
  font-size: 13px;
}
</style>
