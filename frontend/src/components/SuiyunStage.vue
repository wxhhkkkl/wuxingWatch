<script setup lang="ts">
/**
 * 013 期：**一个阶段的岁运结论**（阶段 2 或阶段 3）的呈现。
 *
 * 两页共用： 「加入大运」页贴一份（属大运），「加入流年」页贴两份（属大运 + 属流年）——
 * 同一份实现，故来源标注不可能对不上（FR-024 / SC-008）。
 *
 * **引擎不合成吉凶**（FR-016a）：本组件不产出任何吉凶档位或事件断语，
 * 只把该阶段的结论与依据照实列出。
 */
import { computed } from 'vue'
import type { V2DayunStep, V2Relation } from '../types'
import { wxColor } from '../utils/wuxing'
import StepList from './StepList.vue'

const props = defineProps<{ phase: 'dayun' | 'liunian'; step: V2DayunStep }>()

/** 本阶段**未参与**的那一列：流年（阶段 2 没有它；阶段 3 被大运挡住时后端也不建它）。
 *  判据只能是「快照里有没有这一列」——`step.liunian` 在门控命中时**仍是传入值**，
 *  看它会把被挡住的流年画成一个正常列。 */
const PLACEHOLDERS = [{ key: '_liunian', label: '流年' }]

/** 快照里岁运两列的度数口径（省得把「平加」读成「乘了月令系数」）。 */
const CHART_NOTE = '命盘含本阶段参与的字：大运/流年两列在最左。'
  + '岁运之干为 1 度（即「同类相助 +1」），合而不化者按成数缩放、合化成功改标换字后之字；'
  + '岁运之支的藏干按临大运/临流年独立档**平加**（书 上 884），不乘月令系数。'

const WUXING = ['木', '火', '土', '金', '水'] as const
const GEJU_LABEL: Record<string, string> = {
  zheng: '正格', cong_ruo: '从弱格', cong_qiang: '从强格', cong_yin: '从印格',
  cong_sha: '从杀格', cong_cai: '从财格', hua: '化格',
}
const SOURCE_LABEL = { dayun: '属大运', liunian: '属流年' } as const
/** 每条关系自己的来源阶段（FR-024）——同一阶段内也可能混有属原局的关系。 */
const REL_SRC = { yuanju: '属原局', dayun: '属大运', liunian: '属流年' } as const

/** 该阶段额外参与的干支（阶段 2 为大运，阶段 3 另有流年）。 */
const context = computed(() => {
  const s = props.step
  return s.source === 'liunian'
    ? `大运 ${s.ganzhi}${s.liunian ? ` · 流年 ${s.liunian}` : ''}`
    : `大运 ${s.ganzhi}`
})

const maxScore = computed(() => {
  const vals = WUXING.map((w) => props.step.scores_after?.[w] ?? 0)
  return Math.max(1, ...vals)
})

const tiaohou = computed(() => props.step.tiaohou ?? props.step.yong_shen?.tiaohou ?? null)
const layers = computed(() => props.step.layers ?? null)

const established = computed<V2Relation[]>(
  () => props.step.relations?.established ?? [])
const rejected = computed<V2Relation[]>(
  () => props.step.relations?.rejected ?? [])
</script>

<template>
  <section class="wx-card">
    <p class="wx-card-title">
      {{ phase === 'dayun' ? '加入大运' : '加入流年' }}
      <span class="src-badge" :data-testid="`sy-${phase}-source`">
        {{ SOURCE_LABEL[phase] }}
      </span>
    </p>

    <!-- ① 该阶段参与的干支 + 档位 + 格局 -->
    <div class="verdict-row">
      <span class="verdict-level" :data-testid="`sy-${phase}-level`">{{ step.level }}</span>
      <span class="verdict-class">{{ GEJU_LABEL[step.ge_ju.type] ?? step.ge_ju.type }}</span>
      <span v-if="step.ge_ju.hua_shen" class="verdict-extra">化{{ step.ge_ju.hua_shen }}</span>
      <span v-if="step.transition" class="verdict-extra">{{ step.transition }}</span>
    </div>
    <p class="wx-meta" :data-testid="`sy-${phase}-context`">{{ context }}</p>

    <!-- ② 五行能量条（该阶段增减后的度数） -->
    <div class="energy-list">
      <div v-for="wx in WUXING" :key="wx" class="energy-row">
        <span class="energy-wx" :style="{ color: wxColor(wx) }">{{ wx }}</span>
        <div class="energy-track">
          <div class="energy-fill"
               :style="{ width: Math.min(100, ((step.scores_after?.[wx] ?? 0) / maxScore) * 100) + '%',
                         background: wxColor(wx) }" />
        </div>
        <span class="energy-val">{{ step.scores_after?.[wx] ?? 0 }}</span>
      </div>
    </div>

    <!-- ③ 取用（该阶段重判，FR-016b / FR-021c） -->
    <div class="xi-rows" :data-testid="`sy-${phase}-yong`">
      <div class="xi-row">
        <em>用神</em>
        <span class="xi-val">
          <span v-if="step.yong_shen?.theoretical?.element" class="chip"
                :style="{ background: wxColor(step.yong_shen.theoretical.element) }">
            {{ step.yong_shen.theoretical.element }}
          </span>
          <span v-else class="xi-note">—</span>
          <span v-if="step.yong_shen?.basis" class="xi-note">{{ step.yong_shen.basis }}</span>
        </span>
      </div>
      <div class="xi-row">
        <em>喜神</em>
        <span class="xi-val">
          <span v-for="w in step.yong_shen?.xi_shen ?? []" :key="w" class="chip"
                :style="{ background: wxColor(w) }">{{ w }}</span>
          <span v-if="!(step.yong_shen?.xi_shen ?? []).length" class="xi-note">—</span>
        </span>
      </div>
      <div class="xi-row">
        <em>忌神</em>
        <span class="xi-val">
          <span v-for="w in step.yong_shen?.ji_shen ?? []" :key="w" class="chip chip-plain">{{ w }}</span>
          <span v-if="!(step.yong_shen?.ji_shen ?? []).length" class="xi-note">—</span>
        </span>
      </div>
    </div>

    <!-- ④ 调候量化（FR-021b）——按该阶段同口径重判 -->
    <div class="xi-rows" :data-testid="`sy-${phase}-tiaohou`">
      <div class="xi-row">
        <em>调候</em>
        <span class="xi-val">
          <template v-if="tiaohou">
            <span v-if="tiaohou.element" class="chip"
                  :style="{ background: wxColor(tiaohou.element) }">{{ tiaohou.element }}</span>
            <span v-else class="xi-note">无需调候</span>
            <span class="xi-note">{{ tiaohou.quantified }} · {{ tiaohou.basis }}</span>
          </template>
          <span v-else class="xi-note">—</span>
        </span>
      </div>
    </div>

    <!-- ⑤ 格局层次（FR-021b）——按该阶段同口径重判 -->
    <div class="xi-rows" :data-testid="`sy-${phase}-layers`">
      <div class="xi-row">
        <em>层次</em>
        <span class="xi-val">
          <b v-if="layers?.verdict">{{ layers.verdict }}</b>
          <span class="xi-note">{{ layers?.basis }}</span>
        </span>
      </div>
    </div>
    <div v-if="layers?.met?.length" class="tag-list">
      <span v-for="(m, i) in layers.met" :key="i" class="tag tag-met">✓ {{ m }}</span>
    </div>
    <div v-if="layers?.missing?.length" class="tag-list">
      <span v-for="(m, i) in layers.missing" :key="i" class="tag tag-miss">✗ {{ m }}</span>
    </div>

    <!-- ⑥ 该阶段的关系裁定（含本阶段干支的并入结果） -->
    <div class="rel-block" :data-testid="`sy-${phase}-relations`">
      <p class="rel-head">关系裁定</p>
      <p v-for="(r, i) in established" :key="`e${i}`" class="rel-line">
        <span class="rel-ok">成立</span>
        <em v-if="r.source" class="rel-src">{{ REL_SRC[r.source] }}</em>
        {{ r.type }} · {{ r.detail || r.members.join('') }}
      </p>
      <p v-for="(r, i) in rejected" :key="`r${i}`" class="rel-line rel-off">
        <span class="rel-no">未成立</span>
        <em v-if="r.source" class="rel-src">{{ REL_SRC[r.source] }}</em>
        {{ r.type }} · {{ r.reason || r.detail }}
      </p>
      <p v-if="!established.length && !rejected.length" class="xi-note">本阶段无关系裁定</p>
    </div>

    <!-- ⑦ 判定依据（逐段可读）——与**原局页共用同一份实现**（013 补遗）：
         算式行 → 逐实例快照插在对应算式之后 → 结果 → 五行速览 → 段末命盘。
         命盘比原局页多出大运/流年两列；本阶段未参与的那一列（阶段 2 的流年，
         或被大运挡住的流年）出灰显占位，不伪造度数。 -->
    <StepList v-if="step.steps?.length" :steps="step.steps" :id-prefix="`sy-${phase}`"
              trace-target-color :placeholders="PLACEHOLDERS" :note="CHART_NOTE" />
  </section>
</template>

<style scoped>
.src-badge {
  margin-left: 6px;
  font-size: 12px;
  font-weight: 400;
  color: #fff;
  background: var(--wx-primary-2, #a63431);
  border-radius: 8px;
  padding: 1px 7px;
}
.verdict-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}
.verdict-level {
  font-size: 20px;
  font-weight: 700;
  color: var(--wx-primary-2, #a63431);
}
.verdict-class {
  font-size: 13px;
  color: #fff;
  background: var(--wx-primary-2, #a63431);
  border-radius: 8px;
  padding: 1px 8px;
}
.verdict-extra {
  font-size: 12px;
  color: #8a6a3a;
  background: #fbf5e8;
  border-radius: 8px;
  padding: 1px 8px;
}
.wx-meta {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--wx-muted);
}
.energy-list {
  margin-top: 10px;
}
.energy-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
}
.energy-wx {
  flex: 0 0 1.4em;
  font-size: 15px;
  font-weight: 600;
}
.energy-track {
  flex: 1;
  height: 12px;
  background: #f1ece1;
  border-radius: 6px;
  overflow: hidden;
}
.energy-fill {
  height: 100%;
  border-radius: 6px;
}
.energy-val {
  flex: 0 0 3.4em;
  text-align: right;
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}
.xi-rows {
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin-top: 10px;
}
.xi-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 13px;
}
.xi-row > em {
  flex: 0 0 3.2em;
  font-style: normal;
  font-size: 12px;
  color: var(--wx-muted);
}
.xi-val {
  flex: 1;
  min-width: 0;
}
.xi-note {
  font-size: 12px;
  color: var(--wx-muted);
  line-height: 1.6;
}
.chip {
  display: inline-block;
  min-width: 1.6em;
  padding: 1px 7px;
  margin-right: 4px;
  border-radius: 10px;
  font-size: 12px;
  color: #fff;
  text-align: center;
}
.chip.chip-plain {
  background: #ecebe6;
  color: #6b6b6b;
}
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 6px 0 0;
}
.tag {
  font-size: 12px;
  padding: 3px 8px;
  border-radius: 6px;
}
.tag-met { background: #eef7ee; color: #2f6b35; }
.tag-miss { background: #f7f2ec; color: #8a6a3a; }
.rel-block {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px dashed var(--wx-line);
}
.rel-head {
  margin: 0 0 5px;
  font-size: 12px;
  color: var(--wx-muted);
}
.rel-line {
  margin: 0;
  font-size: 12.5px;
  line-height: 1.7;
}
.rel-line span {
  display: inline-block;
  min-width: 3.4em;
  margin-right: 5px;
  font-size: 11px;
  border-radius: 5px;
  padding: 0 5px;
}
.rel-ok { background: #eef7ee; color: #2f6b35; }
.rel-no { background: #faf0f0; color: #a63431; }
/* 每条关系自己的来源阶段（013 FR-024）——比「成立/未成立」徽标更淡一档 */
.rel-src {
  display: inline-block;
  min-width: auto;
  margin-right: 4px;
  padding: 0 5px;
  border-radius: 5px;
  font-size: 10.5px;
  font-style: normal;
  background: #f1ece1;
  color: #6b6b6b;
}
.rel-off { color: var(--wx-muted); }
/* 判定依据的外壳（.step-*）见 `styles/chart.css`——013 补遗起与**原局页共用一份**，
   本组件不再自带副本（两处的间距/行高曾各写各的、已漂移 10 处）。 */
</style>
