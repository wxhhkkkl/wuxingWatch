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
  //
  // 三类盘要分开对待，不能一刀切：
  //   · **尚未起运**（无大运步）→ 两页都降级——**没有步可选**，阶段 2 无从谈起；
  //   · **无出生日期**（四柱输入）→ 大运**步仍然排得出**（干支序列与起运无关），
  //     但**排不出年份**：定不了「当前所处大运」，也定不了某一步覆盖哪些流年。
  //     故「加入大运」页**照常可用**（按干支选步、不显示年份），只有「加入流年」页降级。
  //   · **时辰不详** → 不阻断，仅明示缺时柱那一维。
  const noSteps = computed(() => !!chart.value && steps.value.length === 0)
  /** 四柱输入模式：排得出大运干支，排不出年份。 */
  const noBirth = computed(() => !!chart.value && !chart.value.solar_birth)
  /** 该步能不能定出年份——「加入流年」页的前提。 */
  const canPickYear = computed(() => currentStep.value?.start_year != null)
  const blocked = computed(() =>
    noSteps.value || (opts.withLiunian === true && !canPickYear.value))
  const degradeReason = computed(() => {
    if (noSteps.value) return '该盘尚未起运，暂无大运可推导'
    if (opts.withLiunian === true && !canPickYear.value) {
      return '该盘由四柱输入排出，没有出生日期，推算不出起运，定不出流年所属的年份'
    }
    return ''
  })
  const notes = computed(() => {
    const out: string[] = []
    if (chart.value?.missing_parts?.includes('hour_pillar')) {
      out.push('时辰不详：缺时柱，岁运结论不含时柱那一维')
    }
    if (noBirth.value && !noSteps.value) {
      out.push('无出生日期：排不出年份，仅按干支选步')
    }
    return out
  })

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
