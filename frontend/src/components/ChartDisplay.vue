<script setup lang="ts">
import { computed } from 'vue'
import type { ChartResult, Pillar } from '../types'

const props = defineProps<{ result: ChartResult }>()

const WX_COLOR: Record<string, string> = {
  木: 'var(--wx-mu)',
  火: 'var(--wx-huo)',
  土: 'var(--wx-tu)',
  金: 'var(--wx-jin)',
  水: 'var(--wx-shui)',
}

function wxColor(wx: string) {
  return WX_COLOR[wx] ?? 'inherit'
}

const pillarNames: Record<string, string> = { year: '年柱', month: '月柱', day: '日柱', time: '时柱' }
const pillarList = computed(() =>
  (['year', 'month', 'day', 'time'] as const).map((key) => ({
    key,
    name: pillarNames[key],
    pillar: props.result.pillars[key] as Pillar | null,
  })),
)

const xi = computed(() => props.result.xi_yong)
</script>

<template>
  <div class="chart">
    <p v-if="result.note" class="note-banner">{{ result.note }}</p>

    <!-- 出生信息 -->
    <section class="wx-card">
      <p class="wx-card-title">出生信息</p>
      <template v-if="result.solar_birth">
        <div class="info-row"><span>公历</span>{{ result.solar_birth.slice(0, 16) }}</div>
        <div class="info-row"><span>农历</span>{{ result.lunar_birth }}</div>
        <div class="info-row"><span>真太阳时</span>{{ result.true_solar_time.slice(0, 16) }}</div>
      </template>
      <template v-else>
        <div class="info-row"><span>方式</span>四柱输入</div>
        <div class="info-row">
          <span>四柱</span>
          {{ result.pillars.year?.ganzhi }} {{ result.pillars.month?.ganzhi }}
          {{ result.pillars.day?.ganzhi }} {{ result.pillars.time?.ganzhi }}
        </div>
      </template>
    </section>

    <!-- 四柱 -->
    <section class="wx-card">
      <p class="wx-card-title">四柱 · 日主 {{ result.day_master }}</p>
      <div class="pillars">
        <div v-for="item in pillarList" :key="item.key" class="pillar" :class="{ dim: !item.pillar }">
          <div class="pillar-label">{{ item.name }}</div>
          <template v-if="item.pillar">
            <div class="pillar-char" :style="{ color: wxColor(item.pillar.gan_wuxing) }">
              {{ item.pillar.gan }}
            </div>
            <div class="pillar-char" :style="{ color: wxColor(item.pillar.zhi_wuxing) }">
              {{ item.pillar.zhi }}
            </div>
            <div class="pillar-shishen">{{ item.pillar.shishen }}</div>
            <div class="pillar-ganzhi">{{ item.pillar.ganzhi }}</div>
          </template>
          <template v-else>
            <div class="pillar-char empty">—</div>
          </template>
        </div>
      </div>
      <p v-if="result.missing_parts.length" class="warn">时辰不详：无法排出时柱、命宫、身宫。</p>
    </section>

    <!-- 人元司令与宫位 -->
    <section class="wx-card">
      <p class="wx-card-title">人元司令 · 胎元 · 宫位</p>
      <div class="info-row">
        <span>人元司令</span>
        藏干 {{ result.hidden_stems.hidden_stems.join('、') }} · 当令 {{ result.hidden_stems.ruling_stem }}
      </div>
      <div class="info-row"><span>胎元</span>{{ result.tai_yuan }}</div>
      <div class="info-row"><span>命宫</span>{{ result.ming_gong ?? '—' }}</div>
      <div class="info-row"><span>身宫</span>{{ result.shen_gong ?? '—' }}</div>
      <p class="muted">{{ result.hidden_stems.source }}</p>
    </section>

    <!-- 大运 -->
    <section class="wx-card">
      <p class="wx-card-title">
        大运<template v-if="result.da_yun.start_age != null"> · {{ result.da_yun.start_age }} 岁起运</template>
      </p>
      <div class="chips">
        <span
          v-for="s in result.da_yun.steps.slice(0, 6)"
          :key="s.ganzhi"
          class="chip"
        >
          {{ s.ganzhi }}
          <small v-if="s.start_year != null">{{ s.start_year }}–{{ s.end_year }}</small>
        </span>
      </div>
    </section>

    <!-- 流年 -->
    <section class="wx-card">
      <p class="wx-card-title">流年</p>
      <div class="chips">
        <span v-for="n in result.liu_nian.slice(0, 6)" :key="n.year" class="chip">
          {{ n.year }} <b>{{ n.ganzhi }}</b>
        </span>
      </div>
    </section>

    <!-- 喜忌分析 -->
    <section class="wx-card">
      <p class="wx-card-title">喜忌分析 · {{ xi.conclusion.summary }}</p>
      <div class="xi-summary">
        <div class="xi-item">
          <span class="xi-label">用神</span>
          <span class="xi-value" :style="{ color: wxColor(xi.conclusion.yong_shen) }">
            {{ xi.conclusion.yong_shen }}
          </span>
        </div>
        <div class="xi-item">
          <span class="xi-label">喜神</span>
          <span class="xi-value">{{ xi.conclusion.xi_shen.join('、') || '—' }}</span>
        </div>
        <div class="xi-item">
          <span class="xi-label">忌神</span>
          <span class="xi-value avoid">{{ xi.conclusion.ji_shen.join('、') || '—' }}</span>
        </div>
      </div>
      <p class="xi-line">
        宜用五行：<b>{{ xi.favorable_elements.join('、') }}</b>
        <span class="muted"> · 忌用：{{ xi.avoid_elements.join('、') || '—' }}</span>
      </p>
      <p class="muted">{{ xi.reasoning }}</p>
      <p class="muted">
        事业：{{ xi.direction.career as string }}；财运：{{ xi.direction.fortune as string }}
      </p>
      <p class="disclaimer">{{ xi.disclaimer }}</p>
    </section>
  </div>
</template>

<style scoped>
.chart {
  padding-bottom: 12px;
}
.note-banner {
  background: #fdf3e0;
  border: 1px solid #ecd9a8;
  color: #8a6d1a;
  border-radius: 10px;
  padding: 10px 12px;
  margin: 12px 14px;
  font-size: 13px;
}
.info-row {
  display: flex;
  gap: 8px;
  font-size: 14px;
  padding: 3px 0;
}
.info-row span {
  color: var(--wx-muted);
  flex: 0 0 68px;
}

/* 四柱 */
.pillars {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.pillar {
  background: #faf6ee;
  border: 1px solid var(--wx-line);
  border-radius: 10px;
  text-align: center;
  padding: 10px 4px 8px;
}
.pillar-label {
  font-size: 12px;
  color: var(--wx-muted);
  margin-bottom: 4px;
}
.pillar-char {
  font-size: 28px;
  font-weight: 600;
  line-height: 1.15;
}
.pillar-char.empty {
  color: var(--wx-line);
}
.pillar-shishen {
  font-size: 11px;
  color: var(--wx-ink);
  margin-top: 3px;
}
.pillar-ganzhi {
  font-size: 11px;
  color: var(--wx-muted);
  margin-top: 1px;
}
.pillar.dim {
  opacity: 0.45;
}

/* 大运 / 流年 chips */
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.chip {
  background: #faf6ee;
  border: 1px solid var(--wx-line);
  border-radius: 14px;
  padding: 5px 10px;
  font-size: 13px;
  color: var(--wx-ink);
}
.chip small {
  color: var(--wx-muted);
  margin-left: 2px;
}

/* 喜忌 */
.xi-summary {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
}
.xi-item {
  flex: 1;
  background: #faf6ee;
  border-radius: 10px;
  text-align: center;
  padding: 8px 4px;
}
.xi-label {
  display: block;
  font-size: 11px;
  color: var(--wx-muted);
}
.xi-value {
  font-size: 20px;
  font-weight: 600;
}
.xi-value.avoid {
  color: var(--wx-primary-2);
}
.xi-line {
  font-size: 14px;
  margin: 6px 0;
}
.muted {
  color: var(--wx-muted);
  font-size: 13px;
}
.warn {
  color: #b8860b;
  font-size: 13px;
  margin-top: 8px;
}
.disclaimer {
  color: var(--wx-muted);
  font-size: 12px;
  margin-top: 8px;
  border-top: 1px dashed var(--wx-line);
  padding-top: 8px;
}
</style>
