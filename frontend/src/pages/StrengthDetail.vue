<script setup lang="ts">
/**
 * **原局旺度**的详细计算过程（2026-10-28 起只保留旺度）。
 *
 * 来源：带 `?record=<id>` 时取那条记录的结果；否则取会话 store 里的排盘。
 * 页面只展示：命盘 → 旺度档位与五行动态/静态 → 逐步依据。
 * 格局、喜忌、用神、调候、岁运推导均已从产品中移除。
 */
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getRecord } from '../api/records'
import { useChartStore } from '../stores/chart'
import PillarBoard from '../components/PillarBoard.vue'
import StepList from '../components/StepList.vue'
import { natalColumns } from '../utils/chartColumns'
import { isWangduV2, type ChartResult } from '../types'
import { wxColor } from '../utils/wuxing'

const router = useRouter()
const route = useRoute()
const chartStore = useChartStore()

const recordResult = ref<ChartResult | null>(null)
const source = computed(() => recordResult.value ?? chartStore.result)

onMounted(async () => {
  const rid = Number(route.query.record)
  if (!rid) return
  try {
    recordResult.value = (await getRecord(rid)).chart_result
  } catch {
    /* 取不到就退回会话 store */
  }
})

const WUXING = ['木', '火', '土', '金', '水'] as const

const v2 = computed(() => {
  const s = source.value?.wan_du
  return isWangduV2(s) ? s : null
})

const pillarList = computed(() => natalColumns(source.value?.pillars))

/** 能量条归一基准：五行动态旺度的最大值（至少 1，避免除零）。 */
const maxScore = computed(() => Math.max(1, ...WUXING.map((w) => v2.value?.final_scores[w] ?? 0)))

/** 日干被天干五合换了字时的**原局那个字**（未换字则 null）。 */
const dmOriginal = computed(() => {
  const o = v2.value?.day_master_original
  return o && o !== v2.value?.day_master ? o : null
})
</script>

<template>
  <div class="detail-page">
    <van-nav-bar title="原局旺度 · 旺度法" left-text="返回" left-arrow @click-left="router.back()" />

    <template v-if="v2">
      <section class="wx-card">
        <p class="wx-card-title">命盘</p>
        <PillarBoard :columns="pillarList" />
      </section>

      <section class="wx-card">
        <p class="wx-card-title">旺度</p>
        <div class="verdict">
          <span class="verdict-level" data-testid="strength-level">{{ v2.level }}</span>
          <span>
            日主 {{ v2.day_master }}
            <template v-if="dmOriginal">（原{{ dmOriginal }}）</template>
            （{{ v2.day_master_wuxing }}）· 动态
            <b>{{ v2.final_scores[v2.day_master_wuxing] }}</b> 度
          </span>
        </div>
        <p class="sum-head">动态旺度（五行合计）</p>
        <div class="bars">
          <div v-for="wx in WUXING" :key="wx" class="bar-row">
            <span class="bar-wx" :style="{ color: wxColor(wx) }">{{ wx }}</span>
            <div class="bar-track">
              <div
                class="bar-fill"
                :style="{
                  width: Math.min(100, ((v2.final_scores[wx] ?? 0) / maxScore) * 100) + '%',
                  background: wxColor(wx),
                }"
              />
            </div>
            <span class="bar-num">{{ v2.final_scores[wx] ?? 0 }}</span>
          </div>
        </div>
        <p class="sum-head">静态旺度（五行合计）</p>
        <p class="static-line">
          <span v-for="wx in WUXING" :key="wx" class="static-item">
            <b :style="{ color: wxColor(wx) }">{{ wx }}</b> {{ v2.static_scores[wx] ?? 0 }}
          </span>
        </p>
        <p v-for="(d, i) in v2.degradations" :key="i" class="warn-line">⚠️ {{ d }}</p>
      </section>

      <section class="wx-card">
        <p class="wx-card-title">逐步依据</p>
        <StepList :steps="v2.steps" id-prefix="wd" :trace-target-color="true" />
      </section>
    </template>

    <van-empty v-else description="暂无原局旺度结果，请重新排盘">
      <van-button type="primary" @click="router.push('/')">去排盘</van-button>
    </van-empty>
  </div>
</template>

<style scoped>
.verdict {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 14px;
  color: var(--wx-text, #333);
}
.verdict-level {
  font-size: 20px;
  font-weight: 600;
  color: var(--wx-primary-2, #a63431);
}
.sum-head {
  margin: 14px 0 6px;
  font-size: 12px;
  color: var(--wx-muted, #888);
}
.bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.bar-wx {
  width: 18px;
  font-weight: 600;
}
.bar-track {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: #f0f0f0;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  border-radius: 4px;
}
.bar-num {
  width: 46px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.static-line {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 13px;
  margin: 0;
}
.static-item b {
  margin-right: 3px;
}
.warn-line {
  margin: 8px 0 0;
  font-size: 12px;
  color: #a15c00;
}
</style>
