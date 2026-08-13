<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useChartStore } from '../stores/chart'
import { wxColor } from '../utils/wuxing'

const router = useRouter()
const chartStore = useChartStore()

const strength = computed(() => chartStore.result?.xi_yong.strength ?? null)

const WUXING = ['木', '火', '土', '金', '水'] as const
</script>

<template>
  <div class="detail-page">
    <van-nav-bar title="强弱分析 · 五行力量评分" left-text="返回" left-arrow @click-left="router.back()" />

    <template v-if="strength">
      <!-- 强弱判定概要 -->
      <section class="wx-card">
        <p class="wx-card-title">强弱判定</p>
        <div class="verdict-row">
          <span class="verdict-level" data-testid="strength-level">{{ strength.level }}</span>
          <span class="verdict-class">{{ strength.classification }}</span>
          <span v-if="strength.cong_ge" class="verdict-cong">从格</span>
        </div>
        <div class="info-row">
          <span>日主</span>{{ strength.day_master }}（{{ strength.day_master_wuxing }}）· 得分
          <b>{{ strength.day_master_score }}</b> / 中和线 {{ strength.balance_line }}
        </div>
        <p v-if="strength.cong_ge" class="muted">弃命从势：日主无生扶，喜克泄耗、忌生扶。</p>

        <!-- 五行分数横条 -->
        <div v-for="wx in WUXING" :key="wx" class="score-row">
          <span class="score-wx" :style="{ color: wxColor(wx) }">{{ wx }}</span>
          <div class="score-bar">
            <div
              class="score-fill"
              :style="{ width: Math.min(100, (strength.scores[wx] ?? 0) / 5.44) + '%', background: wxColor(wx) }"
            />
          </div>
          <span class="score-num">{{ strength.scores[wx] ?? 0 }}</span>
        </div>
      </section>

      <!-- 逐步评分过程 -->
      <section v-for="(s, i) in strength.steps" :key="s.title" class="wx-card">
        <p class="wx-card-title">第 {{ i + 1 }} 步 · {{ s.title }}</p>
        <p class="muted">{{ s.description }}</p>
        <div v-if="s.values" class="step-values">
          <span v-for="(v, wx) in s.values" :key="wx" class="step-val" :style="{ color: wxColor(wx) }">
            {{ wx }} {{ v }}
          </span>
        </div>
      </section>
    </template>

    <van-empty v-else description="暂无强弱评分数据（旧记录可重新排盘获取）">
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
.step-values {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.step-val {
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}
.muted {
  color: var(--wx-muted);
  font-size: 13px;
}
</style>
