/**
 * 014 期：大运引擎2 页的**取数与降级**逻辑。
 *
 * 与 `useSuiyun` 同构，但**只服务于引擎2**（另一个引擎、另一套口径、另一个端点）。
 * 两条来源（FR-006 的「单独入口」）：
 *   - 新排盘结果页（无 `?record=`，取会话 store + `POST /api/charts/dayun2`）；
 *   - 记录详情页（带 `?record=<id>`，取 `GET /api/records/{id}/dayun2`，当场重推）。
 *
 * **结果按需实时算、不落库**（FR-008），故本模块**不读**任何已保存的旺度结论。
 * **不提供并排视图、不提供差异标记**（裁定④）——比对由使用者自己进行。
 */

import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { fetchDayun2 } from '../api/charts'
import { getRecord, getRecordDayun2 } from '../api/records'
import { useChartStore } from '../stores/chart'
import { dayunColumn, natalColumns, type BoardColumn } from './chartColumns'
import type { BirthInput, ChartResult, Dayun2Response, Dayun2Step } from '../types'

export function useDayun2() {
  const route = useRoute()
  const store = useChartStore()

  const recordId = computed(() => {
    const n = Number(route.query.record)
    return Number.isFinite(n) && n > 0 ? n : null
  })

  const chart = ref<ChartResult | null>(null)
  const input = ref<BirthInput | null>(null)
  const sourceError = ref('')
  const sourcePending = ref(true)
  const noChart = computed(() => !sourcePending.value && !chart.value)

  const result = ref<Dayun2Response | null>(null)
  const steps = ref<Dayun2Step[]>([])
  const selectedIndex = ref(0)
  const loading = ref(false)
  const error = ref('')

  /** 该盘的大运步（只取干支与起运信息，**不取**任何旺度结论）。 */
  const dayunSteps = computed(() => (chart.value?.da_yun?.steps ?? []).filter((s) => s.ganzhi))
  const blocked = computed(() => !sourcePending.value && !noChart.value && !dayunSteps.value.length)

  const current = computed<Dayun2Step | null>(() => steps.value[selectedIndex.value] ?? null)
  const elementRows = computed(() =>
    current.value
      ? Object.entries(current.value.elements).map(([wx, v]) => ({ wx, ...v }))
      : [],
  )

  /** 页首命盘卡的列：四柱 ＋ **当前选中那一步**大运（大运居左，与岁运两页同一列序）。
   *
   *  取的是**命盘自己的**大运步（`dayunSteps`），**不是**引擎2 响应里的步：命盘只画字，
   *  与现引擎、与岁运两页看到的是同一张盘，不掺引擎2 的数（否则同一张盘上并排两套数，
   *  违 FR-007）；响应没回来或取失败时，命盘也照常画得出。 */
  const boardColumns = computed<BoardColumn[]>(() => {
    const natal = natalColumns(chart.value?.pillars)
    const step = dayunSteps.value[selectedIndex.value]
    return step ? [dayunColumn(step), ...natal] : natal
  })

  /** **一次取回全部大运步**，切换时只改本地下标、不再发请求。
   *
   *  为什么不是「切一步取一步」：那样后端只回 1 条 `dayun_steps`，而 `current` 是按
   *  `selectedIndex` 取（切到第 2 步就是 `steps[1]`）——数组只剩一条 → `undefined`
   *  → 整块结果空白。实测就是这样「切换后什么都不显示」的。
   *  取全部还顺带满足计划里的「切换大运步须即时响应」（不需每次一个来回）。 */
  async function load() {
    if (!dayunSteps.value.length) return
    loading.value = true
    error.value = ''
    try {
      const resp = recordId.value != null
        ? await getRecordDayun2(recordId.value)
        : await fetchDayun2({ ...(input.value as BirthInput) })
      result.value = resp
      steps.value = resp.dayun_steps
      // 后端按同一批大运步枚举，下标与 `dayunSteps` 一一对应；越界时回退到 0
      if (selectedIndex.value >= steps.value.length) selectedIndex.value = 0
    } catch (e) {
      error.value = (e as Error).message
      steps.value = []
    } finally {
      loading.value = false
    }
  }

  /** 切换大运步——纯本地，**不发请求**（数据一次取回）。 */
  function selectStep(i: number) {
    selectedIndex.value = i
  }

  onMounted(async () => {
    if (recordId.value != null) {
      try {
        chart.value = (await getRecord(recordId.value)).chart_result
      } catch (e) {
        sourceError.value = (e as Error).message
      } finally {
        sourcePending.value = false
      }
    } else {
      chart.value = store.result
      input.value = store.inputs
      sourcePending.value = false
    }
    if (!noChart.value && !blocked.value) await load()
  })

  return {
    recordId, chart, steps: dayunSteps, selectedIndex, selectStep,
    current, elementRows, boardColumns, conclusion: result,
    loading, error, sourceError, noChart, blocked,
  }
}
