<script setup lang="ts">
import { computed } from 'vue'
import type { ChartResult, Pillar } from '../types'

const props = defineProps<{ result: ChartResult }>()

const pillarNames: Record<string, string> = { year: '年柱', month: '月柱', day: '日柱', time: '时柱' }
const rowKeys = ['ganzhi', 'gan_wuxing', 'zhi_wuxing', 'shishen'] as const
const pillarList = computed(() =>
  (['year', 'month', 'day', 'time'] as const).map((key) => ({
    key,
    name: pillarNames[key],
    pillar: props.result.pillars[key] as Pillar | null,
  })),
)
</script>

<template>
  <div class="chart">
    <section class="card">
      <h3>出生信息</h3>
      <p>公历：{{ result.solar_birth.slice(0, 16) }}</p>
      <p>真太阳时：{{ result.true_solar_time.slice(0, 16) }}</p>
      <p>农历：{{ result.lunar_birth }}</p>
    </section>

    <section class="card">
      <h3>四柱（日主 {{ result.day_master }}）</h3>
      <table class="pillars">
        <thead>
          <tr>
            <th v-for="item in pillarList" :key="item.key">{{ item.name }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rowKeys" :key="row">
            <td v-for="item in pillarList" :key="item.key">
              {{ item.pillar ? item.pillar[row] : '—' }}
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="result.missing_parts.length" class="warn">
        时辰不详：无法排出时柱、命宫、身宫。
      </p>
    </section>

    <section class="card">
      <h3>人元司令（{{ result.hidden_stems.branch }}）</h3>
      <p>藏干：{{ result.hidden_stems.hidden_stems.join('、') }} · 当令：{{ result.hidden_stems.ruling_stem }}</p>
      <p class="muted">数据来源：{{ result.hidden_stems.source }}</p>
      <p>胎元：{{ result.tai_yuan }} · 命宫：{{ result.ming_gong ?? '—' }} · 身宫：{{ result.shen_gong ?? '—' }}</p>
    </section>

    <section class="card">
      <h3>大运（{{ result.da_yun.start_age }} 岁起运）</h3>
      <div class="chips">
        <span v-for="s in result.da_yun.steps.slice(0, 6)" :key="s.start_year" class="chip">
          {{ s.ganzhi }} <small>{{ s.start_year }}–{{ s.end_year }}</small>
        </span>
      </div>
    </section>

    <section class="card">
      <h3>流年</h3>
      <div class="chips">
        <span v-for="n in result.liu_nian.slice(0, 6)" :key="n.year" class="chip">
          {{ n.year }} {{ n.ganzhi }}
        </span>
      </div>
    </section>

    <section class="card">
      <h3>喜忌分析（{{ result.xi_yong.conclusion.summary }}）</h3>
      <p>
        用神 <b class="accent">{{ result.xi_yong.conclusion.yong_shen }}</b>
        · 喜神 {{ result.xi_yong.conclusion.xi_shen.join('、') || '—' }}
        · 忌神 {{ result.xi_yong.conclusion.ji_shen.join('、') || '—' }}
      </p>
      <p>宜用五行：{{ result.xi_yong.favorable_elements.join('、') }} · 忌用五行：{{ result.xi_yong.avoid_elements.join('、') || '—' }}</p>
      <p class="muted">{{ result.xi_yong.reasoning }}</p>
      <p class="muted">
        事业：{{ (result.xi_yong.direction.career as string) }}；财运：{{ (result.xi_yong.direction.fortune as string) }}
      </p>
      <p class="muted">{{ result.xi_yong.disclaimer }}</p>
    </section>
  </div>
</template>

<style scoped>
.chart {
  padding: 12px;
}
.card {
  background: #fff;
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}
.card h3 {
  margin: 0 0 10px;
  font-size: 16px;
  color: #8c2f39;
}
.pillars {
  width: 100%;
  border-collapse: collapse;
  text-align: center;
}
.pillars th,
.pillars td {
  border: 1px solid #eee;
  padding: 6px;
  font-size: 14px;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.chip {
  background: #f8f0f0;
  border-radius: 14px;
  padding: 5px 10px;
  font-size: 14px;
}
.muted {
  color: #888;
  font-size: 13px;
}
.warn {
  color: #b8860b;
  font-size: 13px;
}
.accent {
  color: #8c2f39;
}
</style>
