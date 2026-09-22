<script setup lang="ts">
/**
 * 判定依据的**整段列表**（012 v2 建立，013 补遗抽为共享组件）。
 *
 * 原局页与岁运两页共用——包含「算式行 →（逐实例快照插在对应算式之后）→ 结果 →
 * 五行速览 → 段末命盘」这套次序规则，见 `utils/stepRows.ts`。
 *
 * ⚠️ **不得在 `<li>` 的内容外再包任何 wrapper 元素**：既有测试断言的是 `<li>` 的
 * **直接子节点**下标（速览格必须紧邻命盘；逐实例快照必须落在对应算式行与结果行之间）。
 *
 * 根元素即 `<ol class="step-list">`，样式在 `styles/chart.css`。
 */
import type { V2Step } from '../types'
import { ganZhiColor, wxColor } from '../utils/wuxing'
import { stepRows, stepScores } from '../utils/stepRows'
import StepChart from './StepChart.vue'

const props = withDefaults(defineProps<{
  steps: V2Step[]
  /** testid 前缀——原局页 `v2`（与 012 期逐字相同），岁运页 `sy-<阶段>`。 */
  idPrefix?: string
  /** 算式行的 target 是否按五行上色（原局页不上色，岁运页沿用其既有做法）。 */
  traceTargetColor?: boolean
  /** 转发给快照：该阶段**未参与**的字补灰显占位（岁运页的流年列）。 */
  placeholders?: { key: string; label: string }[]
  /** 转发给快照的口径说明。 */
  note?: string
}>(), {
  idPrefix: 'v2', traceTargetColor: false,
  placeholders: () => [], note: '',
})
</script>

<template>
  <ol class="step-list">
    <li v-for="(s, si) in props.steps" :key="s.key" class="step-block"
        :data-testid="`${props.idPrefix}-step-${s.key}`">
      <p class="step-title"><span class="step-no">{{ si + 1 }}</span>{{ s.title }}</p>
      <p class="step-rule">{{ s.rule }}</p>

      <!-- 一段之内的渲染顺序由 `stepRows` 统一决定：算式行 →（第 7 段的逐实例快照
           就插在对应算式之后）→ 结果 → 五行速览 → 段末命盘。速览与命盘相邻。 -->
      <template v-for="(r, ri) in stepRows(s, props.idPrefix)" :key="ri">
        <div v-if="r.kind === 'trace'" class="step-trace">
          <span class="step-trace-target"
                :style="props.traceTargetColor ? { color: ganZhiColor(r.t.target) } : undefined">
            {{ r.t.target }}
          </span>
          <span class="step-trace-expr">{{ r.t.expression }}</span>
          <span v-if="r.t.value !== null && r.t.value !== undefined" class="step-trace-val">{{ r.t.value }}</span>
        </div>

        <div v-else-if="r.kind === 'scores'" class="step-scores"
             :data-testid="`${props.idPrefix}-step-scores`">
          <div v-for="it in stepScores(s)" :key="it.wx" class="score-cell">
            <span class="score-wx step-score-wx" :style="{ color: wxColor(it.wx) }">{{ it.wx }}</span>
            <span class="score-val">{{ it.value ?? '—' }}</span>
          </div>
        </div>

        <p v-else-if="r.kind === 'result'" class="step-result">→ {{ s.result }}</p>

        <!-- 命盘快照：每个天干 / 藏干各多少度，变了的字标出来 -->
        <StepChart v-else :pillars="r.pillars" :label="r.label" :testid="r.testid"
                   :id-prefix="props.idPrefix" :placeholders="props.placeholders"
                   :note="props.note" />
      </template>
    </li>
  </ol>
</template>
