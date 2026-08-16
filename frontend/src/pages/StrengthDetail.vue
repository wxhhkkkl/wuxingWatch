<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useChartStore } from '../stores/chart'
import { isWangduStrength, type WangduStep } from '../types'
import { wxColor } from '../utils/wuxing'

const router = useRouter()
const chartStore = useChartStore()

const strength = computed(() => {
  const s = chartStore.result?.xi_yong.strength
  return isWangduStrength(s) ? s : null
})
const hasLegacy = computed(() => {
  const s = chartStore.result?.xi_yong.strength
  return !!s && !isWangduStrength(s)
})

const WUXING = ['木', '火', '土', '金', '水'] as const
const GEJU_LABEL = { zheng: '正格', cong_ruo: '从弱格', cong_qiang: '从强格', hua: '化格' } as const

// 当前大运介入步：按结果页选中大运（store.viewingDayun），未选取当前年份所在大运，再回退第一步
const currentAdjustment = computed(() => {
  const adjs = strength.value?.dayun_adjustments ?? []
  if (!adjs.length) return null
  const viewing = chartStore.viewingDayun
  if (viewing) {
    const hit = adjs.find((a) => a.ganzhi === viewing)
    if (hit) return hit
  }
  const year = new Date().getFullYear()
  return adjs.find((a) => a.start_year != null && a.start_year <= year && year < a.start_year + 10) ?? adjs[0]
})

// dayun 步的 traces 由当前选中大运的 deltas 动态填充
function stepTraces(s: WangduStep) {
  if (s.key !== 'dayun') return s.traces
  const adj = currentAdjustment.value
  if (!adj) return [{ target: '', expression: '暂无大运数据', value: null }]
  return adj.deltas
}

function stepResult(s: WangduStep) {
  if (s.key !== 'dayun') return s.result
  const adj = currentAdjustment.value
  if (!adj) return '暂无大运数据'
  const dm = strength.value?.day_master_wuxing ?? ''
  return `大运 ${adj.ganzhi}：日主${dm} ${adj.scores_after[dm]} 度 → ${adj.level_after}（仅展示，不改变喜忌结论）`
}
</script>

<template>
  <div class="detail-page">
    <van-nav-bar title="强弱喜忌 · 旺度法（四柱精髓）" left-text="返回" left-arrow @click-left="router.back()" />

    <template v-if="strength">
      <!-- 强弱判定概要 -->
      <section class="wx-card">
        <p class="wx-card-title">强弱与格局</p>
        <div class="verdict-row">
          <span class="verdict-level" data-testid="strength-level">{{ strength.level }}</span>
          <span class="verdict-class">{{ GEJU_LABEL[strength.ge_ju.type] }}</span>
          <span v-if="strength.ge_ju.hua_shen" class="verdict-cong">化{{ strength.ge_ju.hua_shen }}</span>
        </div>
        <div class="info-row">
          <span>日主</span>{{ strength.day_master }}（{{ strength.day_master_wuxing }}）· 最终旺度
          <b>{{ strength.final_scores[strength.day_master_wuxing] }}</b> 度
        </div>

        <!-- 五行最终旺度横条（满刻度 36=旺极线） -->
        <div v-for="wx in WUXING" :key="wx" class="score-row">
          <span class="score-wx" :style="{ color: wxColor(wx) }">{{ wx }}</span>
          <div class="score-bar">
            <div
              class="score-fill"
              :style="{ width: Math.min(100, (strength.final_scores[wx] ?? 0) / 0.36) + '%', background: wxColor(wx) }"
            />
          </div>
          <span class="score-num">{{ strength.final_scores[wx] ?? 0 }}</span>
        </div>
      </section>

      <!-- 逐步推演过程（完整数值轨迹） -->
      <section v-for="(s, i) in strength.steps" :key="s.key" class="wx-card">
        <p class="wx-card-title">第 {{ i + 1 }} 步 · {{ s.title }}</p>
        <p class="muted">{{ s.rule }}</p>
        <div v-for="(t, j) in stepTraces(s)" :key="j" class="trace-row">
          <span v-if="t.target" class="trace-target" :style="{ color: wxColor(t.target) }">{{ t.target }}</span>
          <span class="trace-expr">{{ t.expression }}</span>
          <span v-if="t.value !== null && t.value !== undefined" class="trace-val">{{ t.value }}</span>
        </div>
        <p class="step-result">{{ stepResult(s) }}</p>
      </section>
    </template>

    <van-empty v-else-if="hasLegacy" description="旧版口径的强弱数据，重新排盘可查看新法（旺度法）完整推演">
      <van-button type="primary" @click="router.push('/')">去排盘</van-button>
    </van-empty>
    <van-empty v-else description="暂无强弱分析数据（旧记录可重新排盘获取）">
      <van-button type="primary" @click="router.push('/')">去排盘</van-button>
    </van-empty>
  </div>
</template>

<style scoped>
.verdict-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.verdict-level {
  font-size: 22px;
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
.verdict-cong {
  font-size: 13px;
  color: #b8860b;
  background: #fdf3e0;
  border-radius: 8px;
  padding: 1px 8px;
}
.info-row {
  display: flex;
  gap: 8px;
  font-size: 14px;
  padding: 3px 0;
}
.info-row span {
  color: var(--wx-muted);
  flex: 0 0 44px;
}
.score-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
}
.score-wx {
  flex: 0 0 18px;
  font-size: 15px;
  font-weight: 600;
}
.score-bar {
  flex: 1;
  height: 10px;
  background: #f0ece2;
  border-radius: 5px;
  overflow: hidden;
}
.score-fill {
  height: 100%;
  border-radius: 5px;
}
.score-num {
  flex: 0 0 44px;
  text-align: right;
  font-size: 12px;
  color: var(--wx-muted);
  font-variant-numeric: tabular-nums;
}
.trace-row {
  display: flex;
  gap: 6px;
  font-size: 13px;
  padding: 2px 0;
  align-items: baseline;
}
.trace-target {
  font-weight: 600;
  flex: 0 0 auto;
}
.trace-expr {
  flex: 1;
  color: var(--wx-text, #333);
}
.trace-val {
  color: var(--wx-muted);
  font-variant-numeric: tabular-nums;
}
.step-result {
  margin-top: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--wx-primary-2, #a63431);
}
.muted {
  color: var(--wx-muted);
  font-size: 13px;
}
</style>
