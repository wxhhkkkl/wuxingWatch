<script setup lang="ts">
/**
 * 013 期：「**加入大运**」页（US3 / FR-021）。
 *
 * 三阶段模型的第 2 页——在原局之上加入**选中那一步大运**后重判的关系 / 旺度 /
 * 格局 / 取用 / 调候 / 层次。结论**按需实时算、不落库**（FR-026）；
 * 每项标**来源阶段**「属大运」（FR-024）；引擎**不给吉凶结论**（FR-016a）。
 *
 * 入口两处（FR-021a）：新排盘结果页（无 `?record=`，取会话 store + `POST /api/charts/suiyun`）
 * 与记录详情页（带 `?record=<id>`，取 `GET /api/records/{id}/suiyun`，当场重推）。
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSuiyun } from '../utils/suiyun'
import SuiyunStage from '../components/SuiyunStage.vue'

const router = useRouter()
const { chart, steps, selectedIndex, blocked, degradeReason, notes, sourceError,
        noChart, conclusion, loading, error } = useSuiyun()

const PILLAR_LABEL = { year: '年', month: '月', day: '日', time: '时' } as const
const pillars = computed(() =>
  (['year', 'month', 'day', 'time'] as const)
    .map((k) => ({ key: k, label: PILLAR_LABEL[k], p: chart.value?.pillars?.[k] }))
    .filter((x) => !!x.p))
</script>

<template>
  <div class="detail-page">
    <van-nav-bar title="岁运推导 · 加入大运" left-text="返回" left-arrow @click-left="router.back()" />

    <!-- 来源命盘（四柱） -->
    <section v-if="pillars.length" class="wx-card">
      <p class="wx-card-title">命盘</p>
      <div class="pillar-row">
        <div v-for="it in pillars" :key="it.key" class="pillar-col">
          <span class="pillar-label">{{ it.label }}</span>
          <span class="pillar-ganzhi">{{ it.p!.ganzhi }}</span>
        </div>
      </div>
    </section>

    <!-- 来源命盘不可得：直接打开本页、或记录取不到 -->
    <van-empty v-if="noChart" data-testid="sy-empty" description="暂无可推导的命盘（旧记录可重新排盘获取）">
      <van-button type="primary" @click="router.push('/')">去排盘</van-button>
    </van-empty>

    <p v-else-if="sourceError" class="warn-line">{{ sourceError }}</p>

    <!-- 降级（FR-025）：尚未起运 / 四柱输入且选不了年份——不发请求，直接明示原因 -->
    <van-empty v-else-if="blocked" data-testid="sy-degrade" :description="degradeReason">
      <van-button type="primary" @click="router.back()">返回</van-button>
    </van-empty>

    <template v-else>
      <!-- 选步：该盘的大运步 -->
      <section class="wx-card">
        <p class="wx-card-title">选择大运</p>
        <div class="pick-row">
          <label class="pick-label" for="sy-dayun">大运</label>
          <select id="sy-dayun" v-model.number="selectedIndex"
                  class="pick-select" data-testid="sy-dayun-select">
            <option v-for="(s, i) in steps" :key="s.ganzhi" :value="i">
              {{ s.ganzhi }}{{ s.start_year ? `（${s.start_year} 年起）` : '' }}
            </option>
          </select>
        </div>
        <p v-if="notes.length" class="warn-line">{{ notes.join('；') }}</p>
        <p v-for="(d, i) in conclusion?.degradations ?? []" :key="i" class="warn-line">
          ⚠️ {{ d }}
        </p>
      </section>

      <p class="stage-line" data-testid="sy-stage">阶段 2 · 加入大运</p>

      <van-loading v-if="loading" class="loading" />
      <p v-else-if="error" class="warn-line">{{ error }}</p>
      <SuiyunStage v-else-if="conclusion?.dayun" phase="dayun" :step="conclusion.dayun" />
    </template>
  </div>
</template>

<style scoped>
.loading {
  margin: 30px auto;
}
.warn-line {
  margin: 8px 0 0;
  padding: 6px 8px;
  font-size: 12px;
  line-height: 1.5;
  color: #8a6a3a;
  background: #fdf8ee;
  border-left: 3px solid var(--wx-gold);
  border-radius: 0 6px 6px 0;
}
.stage-line {
  margin: 12px 14px 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--wx-muted);
}
.pick-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
}
.pick-label {
  font-size: 12px;
  color: var(--wx-muted);
}
.pick-select {
  flex: 1;
  font-size: 14px;
  padding: 7px 8px;
  border: 1px solid var(--wx-line);
  border-radius: 8px;
  background: #fff;
  color: var(--wx-ink);
}
.pillar-row {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
.pillar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 9px 0;
  background: #faf7f1;
  border-radius: 10px;
}
.pillar-label {
  font-size: 11px;
  color: var(--wx-muted);
}
.pillar-ganzhi {
  font-size: 18px;
  font-weight: 600;
  font-family: Georgia, "Songti SC", "STSong", "SimSun", serif;
}
</style>
