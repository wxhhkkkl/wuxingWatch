/**
 * 013 期：两个岁运页面（「加入大运」/「加入流年」）的**取数与降级**公共逻辑。
 *
 * 两页的差别只在「要不要带流年」，其余（来源命盘解析、大运步筛选、降级判定、
 * 按需请后端）完全一致——故抽到一处，避免两份实现漂移（011/012 已两度吃亏）。
 *
 * 契约：[contracts/suiyun-v2.md](../../../specs/013-dayun-liunian-judgment/contracts/suiyun-v2.md)；
 * **结论按需实时算、不落库**（FR-026），故本模块**不读**任何已保存的岁运结论。
 */

import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { fetchSuiyun } from '../api/charts'
import { getRecord, getRecordSuiyun } from '../api/records'
import { useChartStore } from '../stores/chart'
import type { BirthInput, ChartResult, SuiyunResponse } from '../types'

/** 一步大运覆盖的 10 年（公历）。 */
function stepYears(startYear: number | null): number[] {
  if (startYear == null) return []
  return Array.from({ length: 10 }, (_, i) => startYear + i)
}

export function useSuiyun(opts: { withLiunian?: boolean } = {}) {
  const route = useRoute()
  const store = useChartStore()

  // ---- 来源：`?record=<id>` 走记录端点（当场重推，FR-021a），否则走会话 store ----
  const recordId = computed(() => {
    const n = Number(route.query.record)
    return Number.isFinite(n) && n > 0 ? n : null
  })
  const chart = ref<ChartResult | null>(null)
  const input = ref<BirthInput | null>(null)
  const sourceError = ref('')

  async function loadSource() {
    if (recordId.value != null) {
      try {
        chart.value = (await getRecord(recordId.value)).chart_result
      } catch (e) {
        sourceError.value = (e as Error).message
      }
      return
    }
    chart.value = store.result
    input.value = store.inputs
  }

  // ---- 选中态：默认当前年份所处的大运步；流年默认该步内的当前年份 ----
  const nowYear = new Date().getFullYear()
  const steps = computed(() => chart.value?.da_yun?.steps ?? [])

  function defaultIndex(): number {
    const i = steps.value.findIndex(
      (s) => s.start_year != null && s.start_year <= nowYear && nowYear < s.start_year + 10,
    )
    return i >= 0 ? i : 0
  }

  const selectedIndex = ref(0)
  const currentStep = computed(() => steps.value[selectedIndex.value] ?? null)
  const years = computed(() => stepYears(currentStep.value?.start_year ?? null))
  const selectedYear = ref<number | null>(null)

  function syncYear() {
    const ys = years.value
    selectedYear.value = ys.includes(nowYear) ? nowYear : (ys[0] ?? null)
  }

  // ---- 降级（FR-025）----
  /** 四柱输入模式：无出生日期 → 算不出起运，岁运推导不可用。 */
  const noBirth = computed(() => !!chart.value && !chart.value.solar_birth)
  /** 尚未起运：无大运步。 */
  const noSteps = computed(() => !!chart.value && steps.value.length === 0)
  const blocked = computed(() => noBirth.value || noSteps.value)
  const degradeReason = computed(() => {
    if (noBirth.value) return '该盘由四柱输入排出，没有出生日期，推算不出起运，岁运推导不可用'
    if (noSteps.value) return '该盘尚未起运，暂无大运可推导'
    return ''
  })
  /** 时辰不详**不阻断**推导（时柱缺失只影响时柱那一维），仅明示。 */
  const notes = computed(() =>
    chart.value?.missing_parts?.includes('hour_pillar')
      ? ['时辰不详：缺时柱，岁运结论不含时柱那一维'] : [])

  // ---- 按需请求 ----
  const conclusion = ref<SuiyunResponse | null>(null)
  const loading = ref(false)
  const error = ref('')

  // 竞态防护：快速切换步/年时丢弃过期响应
  let token = 0
  // 同一次「步 + 年」只请一次——两个 watcher（重置选中态 / 用户改选）会先后触发，
  // 去重后各自都只作一次请求，页面不会因内部复位而多发一遍。
  let lastKey = ''

  async function load() {
    const gz = currentStep.value?.ganzhi
    if (blocked.value || !gz) return
    const year = opts.withLiunian ? selectedYear.value : null
    if (opts.withLiunian && year == null) return
    const key = `${recordId.value}|${gz}|${year}`
    if (key === lastKey) return
    lastKey = key
    const t = ++token
    loading.value = true
    error.value = ''
    try {
      const res = recordId.value != null
        ? await getRecordSuiyun(recordId.value, gz, year ?? undefined)
        : await fetchSuiyun({ ...(input.value as BirthInput), dayun_ganzhi: gz,
                              ...(year != null ? { liunian_year: year } : {}) })
      if (t !== token) return
      conclusion.value = res
    } catch (e) {
      if (t !== token) return
      conclusion.value = null
      error.value = (e as Error).message
      lastKey = ''          // 失败不占位，允许重试同一对参数
    } finally {
      if (t === token) loading.value = false
    }
  }

  // 命盘就位后重置选中态（默认当前年份所处的大运步）
  watch(steps, (list) => {
    selectedIndex.value = defaultIndex()
    if (!list.length) {
      conclusion.value = null
      return
    }
    syncYear()
    void load()
  }, { immediate: true })

  // 用户改选步 / 年
  watch([selectedIndex, selectedYear], () => { void load() })

  onMounted(loadSource)

  return {
    recordId, chart, steps, selectedIndex, currentStep, years, selectedYear,
    blocked, degradeReason, notes, sourceError,
    conclusion, loading, error,
  }
}
