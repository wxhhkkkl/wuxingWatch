<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getRecord } from '../api/records'
import { useChartStore } from '../stores/chart'
import PillarBoard from '../components/PillarBoard.vue'
import StepList from '../components/StepList.vue'
import { natalColumns } from '../utils/chartColumns'
import { isWangduStrength, isWangduV2, type ChartResult, type WangduStep } from '../types'
import { wxColor } from '../utils/wuxing'

const router = useRouter()
const route = useRoute()
const chartStore = useChartStore()

// **来源**：带 `?record=<id>` 时取**那条记录**的结果；否则取当前会话 store 里的排盘。
// 不带来源参数时，从「记录详情」点进来会显示上一次排盘的那张盘（或整页空）——故
// `ChartDisplay` 在记录页会把 id 带过来。
const recordResult = ref<ChartResult | null>(null)
const source = computed(() => recordResult.value ?? chartStore.result)

onMounted(async () => {
  const rid = Number(route.query.record)
  if (!rid) return
  try {
    recordResult.value = (await getRecord(rid)).chart_result
  } catch {
    /* 取不到就退回会话 store（compute 里已兜底为 null） */
  }
})

const strength = computed(() => {
  const s = source.value?.xi_yong.strength
  return isWangduStrength(s) ? s : null
})
const hasLegacy = computed(() => {
  const s = source.value?.xi_yong.strength
  return !!s && !isWangduStrength(s) && !isWangduV2(s)
})

// ---- 012 v2 契约（engine === 'wangdu-v2'）与旧契约**独立渲染路径**（FR-053/054）----
const v2 = computed(() => {
  const s = source.value?.xi_yong.strength
  return isWangduV2(s) ? s : null
})

/** 能量条归一基准：五行中的最大值（至少 1，避免除零）。 */
const maxScore = computed(() => {
  const vals = WUXING.map((w) => v2.value?.degrees[w]?.final ?? 0)
  return Math.max(1, ...vals)
})

/** 当前命盘（八字四柱）。 */
const chart = computed(() => chartStore.result)
const pillarList = computed(() => natalColumns(chart.value?.pillars))

/** 全部大运步。 */
const daYunSteps = computed(() => chart.value?.da_yun?.steps ?? [])

/** 当前大运：优先取结果页选中的，否则按当前年份，再回退第一步。 */
const currentDayun = computed(() => {
  const steps = daYunSteps.value
  if (!steps.length) return null
  const viewing = chartStore.viewingDayun
  if (viewing) {
    const hit = steps.find((d) => d.ganzhi === viewing)
    if (hit) return hit
  }
  const y = new Date().getFullYear()
  return steps.find((d) => d.start_year != null && d.start_year <= y
    && y <= (d.end_year ?? d.start_year + 9)) ?? steps[0]
})

/** 当前流年。 */
const currentLiunian = computed(() => {
  const y = new Date().getFullYear()
  return (chart.value?.liu_nian ?? []).find((l) => l.year === y) ?? null
})

/** 日干被天干五合换了字时的**原局那个字**（未换字则 null）。 */
const dmOriginal = computed(() => {
  const o = v2.value?.day_master_original
  return o && o !== v2.value?.day_master ? o : null
})

const v2Tier = computed(() => {
  const t = v2.value?.yong_shen.tier
  if (!t) return []
  return [['第一', t.first], ['第二', t.second], ['第三', t.third]]
    .filter(([, el]) => !!el) as [string, string][]
})

const WUXING = ['木', '火', '土', '金', '水'] as const
const GEJU_LABEL = { zheng: '正格', cong_ruo: '从弱格', cong_qiang: '从强格', cong_yin: '从印格', cong_sha: '从杀格', cong_cai: '从财格', hua: '化格' } as const

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

    <!-- ============ 012 v2 渲染路径（独立于旧契约） ============ -->
    <template v-if="v2">
      <!-- ① 命盘：八字四柱 + 当前大运 / 流年 -->
      <section class="wx-card">
        <p class="wx-card-title">命盘</p>
        <PillarBoard :columns="pillarList" />
        <div class="luck-row">
          <div class="luck-item">
            <em>当前大运</em>
            <b>{{ currentDayun ? currentDayun.ganzhi : '—' }}</b>
            <span>{{ currentDayun && currentDayun.start_year ? currentDayun.start_year + ' 年起' : '暂无' }}</span>
          </div>
          <div class="luck-item">
            <em>流年</em>
            <b>{{ currentLiunian ? currentLiunian.ganzhi : '—' }}</b>
            <span>{{ currentLiunian ? currentLiunian.year + ' 年' : '暂无' }}</span>
          </div>
        </div>
      </section>

      <!-- ② 强弱与格局：档位 + 五行能量条 -->
      <section class="wx-card">
        <p class="wx-card-title">强弱与格局</p>
        <div class="verdict-row" data-testid="v2-level">
          <span class="verdict-level">{{ v2.level }}</span>
          <span class="verdict-class">{{ GEJU_LABEL[v2.ge_ju.type] }}</span>
          <span v-if="v2.ge_ju.hua_shen" class="verdict-extra">化{{ v2.ge_ju.hua_shen }}</span>
          <span v-if="v2.ge_ju.liang_qi" class="verdict-extra">两气格</span>
        </div>
        <p class="wx-meta" data-testid="v2-dm">
          日主 {{ v2.day_master }}（{{ v2.day_master_wuxing }}）
          <span v-if="dmOriginal" class="pillar-changed" data-testid="v2-dm-original">
            原{{ dmOriginal }}·合化改宗
          </span>
          · 动态旺度 <b>{{ v2.degrees[v2.day_master_wuxing]?.final }}</b> 度
        </p>
        <p v-if="v2.degradations.length" class="warn-line" data-testid="v2-degradations">
          ⚠️ {{ v2.degradations.join('；') }}
        </p>
        <div class="energy-list" data-testid="v2-energy">
          <div
            v-for="wx in WUXING"
            :key="wx"
            class="energy-row"
            :class="{ 'is-dm': wx === v2.day_master_wuxing }"
          >
            <span class="energy-wx" :style="{ color: wxColor(wx) }">{{ wx }}</span>
            <div class="energy-track">
              <div
                class="energy-fill"
                :style="{ width: Math.min(100, ((v2.degrees[wx]?.final ?? 0) / maxScore) * 100) + '%',
                          background: wxColor(wx) }"
              />
            </div>
            <span class="energy-val">{{ v2.degrees[wx]?.final ?? 0 }}</span>
            <span class="energy-state" :title="v2.degrees[wx]?.state">{{ v2.degrees[wx]?.state }}</span>
          </div>
        </div>
        <p class="note-line">能量条以五行最大值为满格；日主一行加重显示。</p>
      </section>

      <!-- ③ 判定依据（紧接强弱与格局）——013 起与岁运两页共用同一份实现 -->
      <section class="wx-card">
        <p class="wx-card-title">判定依据</p>
        <StepList :steps="v2.steps" />
      </section>

      <section class="wx-card">
        <p class="wx-card-title">用神体系（三因素取用）</p>
        <p v-if="v2.yong_shen.empty" class="warn-line" data-testid="v2-empty">无用神可取——此命层次低下</p>
        <template v-else>
          <div class="xi-rows">
            <div class="xi-row">
              <em>理论用神</em>
              <span class="xi-val">
                <span class="chip" :style="{ background: wxColor(v2.yong_shen.theoretical?.element ?? '') }"
                      data-testid="v2-yong">{{ v2.yong_shen.theoretical?.element ?? '—' }}</span>
                <span v-if="v2.yong_shen.practical" class="xi-note" data-testid="v2-practical">
                  实际改用
                  <span class="chip" :style="{ background: wxColor(v2.yong_shen.practical.element ?? '') }">{{ v2.yong_shen.practical.element }}</span>
                  {{ v2.yong_shen.practical.reason }}
                </span>
              </span>
            </div>
            <div class="xi-row">
              <em>喜神</em>
              <span class="xi-val">
                <span v-for="w in v2.yong_shen.xi_shen" :key="w" class="chip"
                      :style="{ background: wxColor(w) }">{{ w }}</span>
                <span v-if="!v2.yong_shen.xi_shen.length" class="xi-note">—</span>
              </span>
            </div>
            <div class="xi-row">
              <em>忌神</em>
              <span class="xi-val">
                <span v-for="w in v2.yong_shen.ji_shen" :key="w" class="chip chip-plain">{{ w }}</span>
                <span v-if="!v2.yong_shen.ji_shen.length" class="xi-note">—</span>
              </span>
            </div>
            <div v-if="v2.yong_shen.xian_shen.length" class="xi-row">
              <em>闲神</em>
              <span class="xi-val">
                <span v-for="w in v2.yong_shen.xian_shen" :key="w" class="chip chip-plain">{{ w }}</span>
              </span>
            </div>
            <div v-if="v2Tier.length" class="xi-row">
              <em>用神层次</em>
              <span class="xi-val">
                <span v-for="[n, el] in v2Tier" :key="n" class="tier-item">
                  <span class="tier-name">{{ n }}</span>
                  <span class="chip" :style="{ background: wxColor(el) }">{{ el }}</span>
                </span>
              </span>
            </div>
          </div>
          <p class="note-line" data-testid="v2-yong-basis">{{ v2.yong_shen.basis }}</p>
        </template>
      </section>

      <section v-if="v2.yong_shen.tiaohou" class="wx-card">
        <p class="wx-card-title">调候</p>
        <div class="xi-rows">
          <div class="xi-row">
            <em>调候用神</em>
            <span class="xi-val">
              <span v-if="v2.yong_shen.tiaohou.element" class="chip"
                    :style="{ background: wxColor(v2.yong_shen.tiaohou.element) }">{{ v2.yong_shen.tiaohou.element }}</span>
              <span v-else class="xi-note">本月无需调候</span>
            </span>
          </div>
          <div class="xi-row" data-testid="v2-tiaohou">
            <em>是否得调候</em>
            <span class="xi-val">
              <span :class="['tag', v2.yong_shen.tiaohou.met ? 'tag-met' : 'tag-pen']">
                {{ v2.yong_shen.tiaohou.met ? '已得调候' : '需调候而无调候' }}
              </span>
              <span class="xi-note">{{ v2.yong_shen.tiaohou.quantified }}</span>
            </span>
          </div>
        </div>
        <p class="note-line">{{ v2.yong_shen.tiaohou.basis }}</p>
      </section>

      <section v-if="v2.layers" class="wx-card">
        <p class="wx-card-title">格局层次</p>
        <p v-if="v2.layers.verdict" class="wx-meta"><b>{{ v2.layers.verdict }}</b></p>
        <p class="note-line" data-testid="v2-layers-basis">{{ v2.layers.basis }}</p>
        <div v-if="v2.layers.met.length" class="tag-list">
          <span v-for="(m, i) in v2.layers.met" :key="i" class="tag tag-met">✓ {{ m }}</span>
        </div>
        <div v-if="v2.layers.missing.length" class="tag-list">
          <span v-for="(m, i) in v2.layers.missing" :key="i" class="tag tag-miss">✗ {{ m }}</span>
        </div>
        <div v-if="v2.layers.penalties.length" class="tag-list">
          <span v-for="(p, i) in v2.layers.penalties" :key="i" class="tag tag-pen">
            {{ p.delta }}　{{ p.reason }}
          </span>
        </div>
      </section>

      <section v-if="v2.dayun.length" class="wx-card">
        <p class="wx-card-title">用神随大运变化</p>
        <div v-for="d in v2.dayun" :key="d.ganzhi" class="dayun-row" data-testid="v2-dayun-row">
          <div class="dayun-head">
            <b class="dayun-gz">{{ d.ganzhi }}</b>
            <span class="dayun-year">{{ d.start_year ? d.start_year + ' 年起' : '—' }}</span>
            <span v-if="d.transition" class="tag tag-pen">{{ d.transition }}</span>
          </div>
          <div class="dayun-body">
            <span v-if="d.yong_shen?.theoretical?.element" class="chip"
                  :style="{ background: wxColor(d.yong_shen.theoretical.element) }">{{ d.yong_shen.theoretical.element }}</span>
            <span v-else class="chip chip-plain">—</span>
            <span class="xi-note">
              {{ d.level }} · {{ GEJU_LABEL[d.ge_ju.type] }}<template v-if="d.ge_ju.hua_shen">（化{{ d.ge_ju.hua_shen }}）</template>
            </span>
          </div>
        </div>
      </section>

    </template>

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

/* ==== 012 v2：当前大运 / 流年两格（命盘柱列见 styles/chart.css）==== */
.luck-row {
  display: flex;
  gap: 8px;
}
.luck-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 7px 10px;
  background: #faf7f1;
  border-radius: 10px;
}
.luck-item em {
  font-style: normal;
  font-size: 11px;
  color: var(--wx-muted);
}
.luck-item b {
  font-size: 17px;
  color: var(--wx-ink);
  font-family: Georgia, "Songti SC", "STSong", "SimSun", serif;
}
.luck-item span {
  font-size: 11px;
  color: var(--wx-muted);
}

/* ==== 012 v2：结论档位 + 五行能量条 ==== */
.wx-meta {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--wx-muted);
}
.wx-meta b {
  font-size: 13px;
  color: var(--wx-ink);
}
.verdict-extra {
  font-size: 12px;
  color: #8a6a3a;
  background: #fbf5e8;
  border-radius: 8px;
  padding: 1px 8px;
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
.energy-list {
  margin-top: 10px;
}
.energy-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 6px;
  border-radius: 8px;
}
.energy-row.is-dm {
  background: #faf7f1;
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
  transition: width 0.25s ease;
}
.energy-val {
  flex: 0 0 3.4em;
  text-align: right;
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}
/* 状态列：值来自 `degrees[wx].state`，正常是「余气」这类短名，但月令合化取平均时
   会是「相与旺」这种两名并列——列宽吃过窄会把整行撑成多行，故给弹性宽度 + 截断。 */
.energy-state {
  flex: 0 1 auto;
  max-width: 5.5em;
  text-align: right;
  font-size: 11px;
  color: var(--wx-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.energy-row.is-dm .energy-wx,
.energy-row.is-dm .energy-val {
  font-weight: 700;
}

/* ==== 012 v2：标签化行（用神 / 调候 / 大运）==== */
.xi-rows {
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin-top: 8px;
}
.xi-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 13px;
}
.xi-row > em {
  flex: 0 0 4.5em;
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
.tier-item {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  margin-right: 10px;
}
.tier-name {
  font-size: 12px;
  color: var(--wx-muted);
}
.note-line {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--wx-muted);
  line-height: 1.6;
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
  line-height: 1.5;
}
.tag-met { background: #eef7ee; color: #2f6b35; }
.tag-miss { background: #f7f2ec; color: #8a6a3a; }
.tag-pen { background: #faf0f0; color: #a63431; }

/* 用神随大运变化 */
.dayun-row {
  padding: 9px 10px;
  margin-bottom: 8px;
  background: #faf7f1;
  border-radius: 10px;
}
.dayun-row:last-child {
  margin-bottom: 0;
}
.dayun-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 5px;
}
.dayun-gz {
  font-size: 16px;
  color: var(--wx-ink);
  font-family: Georgia, "Songti SC", "STSong", "SimSun", serif;
}
.dayun-year {
  flex: 1;
  font-size: 11px;
  color: var(--wx-muted);
}
.dayun-body {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 命盘柱列族与判定依据分步卡片族见 `styles/chart.css`（013 补遗：与原局/岁运两页共用） */
</style>
