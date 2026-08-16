<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ChartResult, DaYunStep, LiuNianStep } from '../types'
import {
  buildPillarNodes,
  buildFlowArrows,
  buildRelationJudgments,
  LEGEND,
  PALACE_ROLE,
  relativeOf,
  REL_TYPES,
  type FlowType,
  type Judgment,
  type PillarKey,
  type RelCol,
  type RelPair,
  type RelType,
} from '../utils/relations'
import { GAN_WUXING, wxColor, ZHI_WUXING } from '../utils/wuxing'

const props = defineProps<{
  result: ChartResult
  selectedDayun?: DaYunStep | null
  selectedLiunian?: LiuNianStep | null
}>()

type TabKey = 'guanxi' | 'liutong' | 'gongwei' | 'liuqin'
const TABS: { key: TabKey; label: string }[] = [
  { key: 'guanxi', label: '关系' },
  { key: 'liutong', label: '流通' },
  { key: 'gongwei', label: '宫位' },
  { key: 'liuqin', label: '六亲' },
]
const activeTab = ref<TabKey>('guanxi')

const pillarNodes = computed(() => buildPillarNodes(props.result))
const flowArrows = computed(() => buildFlowArrows(props.result.pillars))
const anyMissing = computed(() => pillarNodes.value.some((n) => !n.present))

const ARROW_TEXT: Record<FlowType, string> = { sheng: '生', ke: '克', bi: '比' }

// 关系筛选两行（天干 / 地支），内部类型分层专属
const GAN_REL_TYPES: RelType[] = ['生', '克', '合', '合化', '冲']
const ZHI_REL_TYPES: RelType[] = ['三会', '三合', '六合', '相冲', '刑', '害', '破']
// 显示名：天干「合→五合、冲→相冲」，地支「刑→相刑、害→六害、破→相破」
const GAN_LABEL: Record<string, string> = { 生: '相生', 克: '相克', 合: '五合', 合化: '合化', 冲: '相冲' }
const ZHI_LABEL: Record<string, string> = { 三会: '三会', 三合: '三合', 六合: '六合', 相冲: '相冲', 刑: '相刑', 害: '六害', 破: '相破' }

// ---------- 关系图（干支/藏干 节点 + 合冲刑破害克 连线） ----------

// 关系列：大运、流年、年/月/日/时（大运流年在最左，四柱在后）
const relCols = computed<RelCol[]>(() => {
  const cols: RelCol[] = []
  const dy = props.selectedDayun
  if (dy?.ganzhi) {
    const gan = dy.gan ?? dy.ganzhi[0]
    const zhi = dy.zhi ?? dy.ganzhi[1]
    cols.push({
      id: 'dayun', label: '大运',
      gan, ganWx: GAN_WUXING[gan] ?? '',
      zhi, zhiWx: ZHI_WUXING[zhi] ?? '',
      canggan: (dy.detail?.cang_gan ?? []).map((c) => ({ gan: c.gan, wx: GAN_WUXING[c.gan] ?? '' })),
    })
  }
  const ln = props.selectedLiunian
  if (ln?.ganzhi) {
    const gan = ln.gan ?? ln.ganzhi[0]
    const zhi = ln.zhi ?? ln.ganzhi[1]
    cols.push({
      id: 'liunian', label: '流年',
      gan, ganWx: GAN_WUXING[gan] ?? '',
      zhi, zhiWx: ZHI_WUXING[zhi] ?? '',
      canggan: (ln.detail?.cang_gan ?? []).map((c) => ({ gan: c.gan, wx: GAN_WUXING[c.gan] ?? '' })),
    })
  }
  for (const n of pillarNodes.value) {
    cols.push({
      id: n.key, label: n.label.replace('柱', ''),
      gan: n.gan, ganWx: n.ganWx,
      zhi: n.zhi, zhiWx: n.zhiWx,
      canggan: n.hiddenStems.map((h) => ({ gan: h.gan, wx: h.wx })),
    })
  }
  return cols
})

// 008：条件判定（成立/未成立）→ 连线只画成立关系
const relJudgments = computed(() =>
  buildRelationJudgments(relCols.value, {
    excludeColIds: includeDayunLiunian.value ? [] : ['dayun', 'liunian'],
  }),
)

/** 判定条目 → 连线/汇总用的 RelPair（显示文案在此组装）。 */
function toRelPair(j: Judgment): RelPair {
  if (j.layer === 'stem') {
    const type: RelType = j.type === '五合' ? (j.detail?.startsWith('合化') ? '合化' : '合') : (j.type as RelType)
    const detail = j.type === '五合' ? `${j.a}${j.b}${j.detail}` : (j.detail ?? '')
    return { a: `gan-${j.aColId}`, b: `gan-${j.bColId}`, type, detail, aChar: j.a, bChar: j.b }
  }
  // 三支关系：锚定单节点，横跨逻辑在 zhiEdges
  if (j.members) {
    const label = j.members.join('')
    const anchor = `zhi-${j.memberColIds![0]}`
    const detail = j.detail === '合绊' ? `${label}${j.type}·合绊` : `${label}${j.detail}`
    return { a: anchor, b: anchor, type: j.type as RelType, detail, aChar: label, bChar: '' }
  }
  const a = `zhi-${j.aColId}`
  const b = `zhi-${j.bColId}`
  const base = { a, b, aChar: j.a, bChar: j.b }
  switch (j.type) {
    case '六合':
      return { ...base, type: '六合', detail: j.detail!.startsWith('合化') ? `${j.a}${j.b}${j.detail}` : `${j.a}${j.b}合·${j.detail}` }
    case '相冲':
      return { ...base, type: '相冲', detail: `${j.a}${j.b}相冲` }
    case '半三合':
      return { ...base, type: '三合', detail: j.detail!.startsWith('合化') ? `${j.a}${j.b}半合化${j.detail!.slice(2)}` : `${j.a}${j.b}半合·${j.detail}` }
    case '刑':
      return { ...base, type: '刑', detail: j.a === j.b ? `${j.a}${j.b}自刑` : `${j.a}${j.b}相刑` }
    case '害':
      return { ...base, type: '害', detail: `${j.a}${j.b}相害` }
    default:
      return { ...base, type: '破', detail: `${j.a}${j.b}相破` }
  }
}

const relPairs = computed<RelPair[]>(() => relJudgments.value.established.map(toRelPair))

// 未成立关系（判定不成立：隔位/被让位/条件不足等），汇总区单列分组
const REJ_SHORT: Record<string, string> = {
  五合: '合', 冲: '冲', 生: '生', 克: '克',
  六合: '合', 相冲: '冲', 半三合: '半合', 三合: '三合', 三会: '三会',
  三刑: '三刑', 刑: '刑', 害: '害', 破: '破',
}
const rejectedItems = computed<string[]>(() => {
  const seen = new Set<string>()
  for (const j of relJudgments.value.rejected) {
    const label = j.members ? j.members.join('') + j.type : `${j.a}${j.b}${REJ_SHORT[j.type] ?? j.type}`
    seen.add(`${label} · ${j.reason}`)
  }
  return [...seen]
})

// 关系类型筛选（多选；未勾选任何类型时不画连线）
const selectedTypes = ref<RelType[]>([])
function toggleType(t: RelType) {
  const i = selectedTypes.value.indexOf(t)
  if (i >= 0) selectedTypes.value.splice(i, 1)
  else selectedTypes.value.push(t)
}
// 是否关联大运/流年（仅影响连线是否含大运/流年，列显示不变）
const includeDayunLiunian = ref(true)
const visiblePairs = computed<RelPair[]>(() => {
  const sel = new Set(selectedTypes.value)
  return relPairs.value.filter((p) => sel.has(p.type))
})

// 当前命盘存在的关系汇总（按类型去重，再分天干/地支两组）
const relSummary = computed(() => {
  const byType = new Map<RelType, Set<string>>()
  for (const p of relPairs.value) {
    if (!byType.has(p.type)) byType.set(p.type, new Set())
    byType.get(p.type)!.add(p.detail)
  }
  const mk = (types: RelType[]) =>
    types.filter((t) => byType.has(t)).map((t) => ({ type: t, items: [...byType.get(t)!] }))
  return {
    gan: mk(GAN_REL_TYPES),
    zhi: mk(ZHI_REL_TYPES),
  }
})

// ---------- 布局：中间八字行 + 上（干）/下（支）两层关系连线（纯 CSS 定位） ----------

// 各列位置按容器宽度百分比（一屏收进，不横向滚动）
const nCols = computed(() => relCols.value.length)
const EDGE_GAP = 20 // 每条关系连线纵向间距
const EDGE_H = 14 // 单条连线高度
const colWidthPct = computed(() => 100 / nCols.value)
const colLeftPct = (i: number) => i * colWidthPct.value
const colCenterPct = (i: number) => (i + 0.5) * colWidthPct.value
const colIndexOf = (colId: string) => relCols.value.findIndex((c) => c.id === colId)
const topHeight = computed(() => ganEdges.value.length * EDGE_GAP + 4)
const bottomHeight = computed(() => zhiEdges.value.length * EDGE_GAP + 4)

interface EdgeLine {
  left: number
  width: number
  label: string // 干支字（如 乙庚 / 子午）
  type: RelType
  detail: string
}

// 干层连线（八字上方，自底向上堆叠）
const ganEdges = computed<EdgeLine[]>(() => {
  const list = visiblePairs.value.filter((p) => p.a.startsWith('gan-'))
  return list.map((p) => {
    const x1 = colCenterPct(colIndexOf(p.a.slice(4)))
    const x2 = colCenterPct(colIndexOf(p.b.slice(4)))
    return {
      left: Math.min(x1, x2), width: Math.abs(x2 - x1),
      label: `${p.aChar}${p.bChar}`, type: p.type, detail: p.detail,
    }
  })
})

// 地支成局（三合/三会）各组的支集合，用于把连线横跨到该组覆盖的列范围
const SAN_HE_SETS: Set<string>[] = [
  new Set(['申', '子', '辰']), new Set(['亥', '卯', '未']),
  new Set(['寅', '午', '戌']), new Set(['巳', '酉', '丑']),
]
const SAN_HUI_SETS: Set<string>[] = [
  new Set(['亥', '子', '丑']), new Set(['寅', '卯', '辰']),
  new Set(['巳', '午', '未']), new Set(['申', '酉', '戌']),
]

// 支层连线（八字下方，自顶向下堆叠），三会/三合横跨其覆盖的列范围
const zhiEdges = computed<EdgeLine[]>(() => {
  const list = visiblePairs.value.filter((p) => p.a.startsWith('zhi-'))
  const lines: EdgeLine[] = []
  list.forEach((p) => {
    if (p.a === p.b) {
      // 成局（三合/三会）：横跨该组三支覆盖的列范围
      const sets = p.type === '三合' ? SAN_HE_SETS : SAN_HUI_SETS
      const set = sets.find((s) => [...s].every((b) => p.aChar.includes(b)))
      const idxs = relCols.value
        .map((c, i) => (set?.has(c.zhi) ? i : -1))
        .filter((i) => i >= 0)
      const first = idxs.length ? Math.min(...idxs) : colIndexOf(p.a.slice(4))
      const last = idxs.length ? Math.max(...idxs) : colIndexOf(p.a.slice(4))
      const left = colLeftPct(first)
      const right = colLeftPct(last) + colWidthPct.value
      lines.push({ left, width: right - left, label: p.aChar, type: p.type, detail: p.detail })
      return
    }
    const x1 = colCenterPct(colIndexOf(p.a.slice(4)))
    const x2 = colCenterPct(colIndexOf(p.b.slice(4)))
    lines.push({
      left: Math.min(x1, x2), width: Math.abs(x2 - x1),
      label: `${p.aChar}${p.bChar}`, type: p.type, detail: p.detail,
    })
  })
  return lines
})

const PAIR_COLOR: Record<RelType, string> = {
  生: '#2e7d32', // 绿
  克: '#8a5a2b', // 棕
  合: '#1b7a3d', // 深绿
  合化: '#00796b', // 青
  冲: '#c62828', // 红
  三会: '#00695c', // 深青
  三合: '#2e7d32', // 绿
  六合: '#558b2f', // 黄绿
  相冲: '#ad1457', // 品红
  刑: '#e65100', // 橙
  害: '#6d4c41', // 深棕
  破: '#8e24aa', // 紫
}

// 流通网格列 = 起始柱的节点序号 → 列位置（节点占奇数列，箭头占偶数列）
function colOf(from: PillarKey): number {
  return pillarNodes.value.findIndex((n) => n.key === from) * 2 + 2
}
</script>

<template>
  <section class="wx-card" data-testid="relation-diagram">
    <p class="wx-card-title rd-title">
      命盘图
      <label class="rd-dy-toggle rd-dy-toggle--title">
        <input v-model="includeDayunLiunian" type="checkbox" data-testid="toggle-dayun" />
        关联大运/流年
      </label>
    </p>
    <div class="rd">
      <div class="rd-tabs" role="tablist">
      <button
        v-for="t in TABS"
        :key="t.key"
        type="button"
        class="rd-tab"
        :class="{ 'rd-tab--active': activeTab === t.key }"
        :data-testid="`tab-${t.key}`"
        @click="activeTab = t.key"
      >
        {{ t.label }}
      </button>
    </div>

    <!-- 关系 tab：干支/藏干 节点 + 合冲刑破害克 连线（含大运/流年） -->
    <div v-if="activeTab === 'guanxi'" class="rd-panel" data-testid="panel-guanxi">
      <!-- 关系类型筛选（天干 / 地支 两行，多选） -->
      <div class="rd-filter-group">
        <span class="rd-filter-label">天干</span>
        <button
          v-for="t in GAN_REL_TYPES"
          :key="`g-${t}`"
          type="button"
          class="rd-filter"
          :class="{ 'rd-filter--active': selectedTypes.includes(t) }"
          :data-testid="`filter-gan-${t}`"
          @click="toggleType(t)"
        >
          {{ GAN_LABEL[t] ?? t }}
        </button>
      </div>
      <div class="rd-filter-group">
        <span class="rd-filter-label">地支</span>
        <button
          v-for="t in ZHI_REL_TYPES"
          :key="`z-${t}`"
          type="button"
          class="rd-filter"
          :class="{ 'rd-filter--active': selectedTypes.includes(t) }"
          :data-testid="`filter-zhi-${t}`"
          @click="toggleType(t)"
        >
          {{ ZHI_LABEL[t] ?? t }}
        </button>
      </div>

      <!-- 关系图（纯 CSS 定位，一屏收进） -->
      <div class="rd-rel" data-testid="rel-svg">
        <!-- 天干关系（八字上方，贴近八字自底向上堆叠） -->
        <div class="rd-edges rd-edges--top" :style="{ height: topHeight + 'px' }">
          <div
            v-for="(e, i) in ganEdges"
            :key="`gan-${i}`"
            class="rd-edge"
            :class="`rd-edge--${e.type}`"
            :data-type="e.type"
            :data-testid="`edge-gan-${i}`"
            :style="{ left: e.left + '%', width: Math.max(e.width, 4) + '%', bottom: i * EDGE_GAP + 'px' }"
          >
            <span class="rd-edge-tag">{{ e.label }}</span>
          </div>
        </div>

        <!-- 八字行（大运/流年/年/月/日/时，干在上、支在下） -->
        <div class="rd-bazi">
          <div
            v-for="(c, i) in relCols"
            :key="c.id"
            class="rd-bazi-col"
            :style="{ width: colWidthPct + '%' }"
          >
            <span class="rd-bazi-hdr">{{ c.label }}</span>
            <span
              class="rd-bazi-char"
              :style="{ color: c.ganWx ? wxColor(c.ganWx) : 'inherit' }"
              :data-testid="`node-gan-${c.id}`"
              >{{ c.gan }}</span
            >
            <span
              class="rd-bazi-char"
              :style="{ color: c.zhiWx ? wxColor(c.zhiWx) : 'inherit' }"
              :data-testid="`node-zhi-${c.id}`"
              >{{ c.zhi }}</span
            >
            <!-- 藏干（地支下方，纯展示） -->
            <span class="rd-bazi-zang" :data-testid="`zang-${c.id}`">
              <span
                v-for="(h, zi) in c.canggan"
                :key="zi"
                class="rd-bazi-zang-char"
                :style="{ color: h.wx ? wxColor(h.wx) : 'inherit' }"
                >{{ h.gan }}</span
              >
            </span>
          </div>
        </div>

        <!-- 地支关系（八字下方，自顶向下堆叠） -->
        <div class="rd-edges rd-edges--bottom" :style="{ height: bottomHeight + 'px' }">
          <div
            v-for="(e, i) in zhiEdges"
            :key="`zhi-${i}`"
            class="rd-edge"
            :class="`rd-edge--${e.type}`"
            :data-type="e.type"
            :data-testid="`edge-zhi-${i}`"
            :style="{ left: e.left + '%', width: Math.max(e.width, 4) + '%', top: i * EDGE_GAP + 'px' }"
          >
            <span class="rd-edge-tag">{{ e.label }}</span>
          </div>
        </div>
      </div>

      <!-- 当前命盘关系汇总（分天干/地支） -->
      <div class="rd-rel-summary" data-testid="rel-summary">
        <div class="rd-rel-summary-title">本盘关系</div>
        <div class="rd-rel-summary-group">
          <span class="rd-filter-label">天干</span>
          <div class="rd-rel-summary-rows">
            <div v-for="g in relSummary.gan" :key="g.type" class="rd-rel-summary-row" :data-testid="`summary-${g.type}`">
              <b class="rd-rel-summary-type" :style="{ color: PAIR_COLOR[g.type] }">{{ GAN_LABEL[g.type] ?? g.type }}</b>
              <span class="rd-rel-summary-items">{{ g.items.join('、') }}</span>
            </div>
          </div>
        </div>
        <div class="rd-rel-summary-group">
          <span class="rd-filter-label">地支</span>
          <div class="rd-rel-summary-rows">
            <div v-for="g in relSummary.zhi" :key="g.type" class="rd-rel-summary-row" :data-testid="`summary-${g.type}`">
              <b class="rd-rel-summary-type" :style="{ color: PAIR_COLOR[g.type] }">{{ ZHI_LABEL[g.type] ?? g.type }}</b>
              <span class="rd-rel-summary-items">{{ g.items.join('、') }}</span>
            </div>
          </div>
        </div>
        <!-- 008：判定未成立的关系（隔位/被让位/条件不足等），单列分组附原因 -->
        <div v-if="rejectedItems.length" class="rd-rel-summary-group">
          <span class="rd-filter-label">未成立</span>
          <div class="rd-rel-summary-rows">
            <div class="rd-rel-summary-row" data-testid="summary-rejected">
              <span class="rd-rel-summary-items rd-rel-rejected">{{ rejectedItems.join('、') }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 流通 tab：干支双层流通箭头 -->
    <div v-if="activeTab === 'liutong'" class="rd-panel" data-testid="panel-liutong">
      <div class="rd-grid">
        <template v-for="(node, i) in pillarNodes" :key="node.key">
          <div
            class="rd-flow-pillar"
            :style="{ gridColumn: i * 2 + 1, gridRow: '1 / span 2' }"
          >
            <span class="rd-gz-label">{{ node.label }}</span>
            <template v-if="node.present">
              <span
                class="rd-char"
                :style="{ color: node.ganWx ? wxColor(node.ganWx) : 'inherit' }"
                >{{ node.gan }}</span
              >
              <span
                class="rd-char"
                :style="{ color: node.zhiWx ? wxColor(node.zhiWx) : 'inherit' }"
                >{{ node.zhi }}</span
              >
            </template>
            <span v-else class="rd-char rd-char--none">—</span>
          </div>
        </template>
        <template v-for="arrow in flowArrows" :key="`${arrow.layer}-${arrow.from}-${arrow.to}`">
          <div
            class="rd-arrow"
            :class="`rd-arrow--${arrow.type}`"
            :data-type="arrow.type"
            :data-testid="`arrow-${arrow.layer}-${arrow.from}-${arrow.to}`"
            :style="{ gridColumn: colOf(arrow.from), gridRow: arrow.layer === 'gan' ? 1 : 2 }"
          >
            <span class="rd-arrow-sym">→</span
            ><span class="rd-arrow-label">{{ ARROW_TEXT[arrow.type] }}</span>
          </div>
        </template>
      </div>
      <p class="rd-flow-note">箭头：相生(绿) → 相克(红) → 比和(灰)（颜色 + 文字双重标注）</p>
    </div>

    <!-- 宫位 tab：宫位映射表 -->
    <div v-if="activeTab === 'gongwei'" class="rd-panel" data-testid="panel-gongwei">
      <div v-for="node in pillarNodes" :key="node.key" class="rd-row">
        <span class="rd-row-label">{{ node.label }}</span>
        <span class="rd-row-value" :data-testid="`palace-${node.key}`">{{
          node.present ? node.palace : '—'
        }}</span>
        <span class="rd-row-desc">{{ node.present ? PALACE_ROLE[node.key] : '时辰不详' }}</span>
      </div>
    </div>

    <!-- 六亲 tab：本命十神→六亲 + 图例 -->
    <div v-if="activeTab === 'liuqin'" class="rd-panel" data-testid="panel-liuqin">
      <div v-for="node in pillarNodes" :key="node.key" class="rd-row">
        <span class="rd-row-label">{{ node.label }}</span>
        <span class="rd-row-value" :data-testid="`god-${node.key}`">{{
          node.present ? node.ganShishen : '—'
        }}</span>
        <span class="rd-row-desc" :data-testid="`relative-${node.key}`">{{
          node.present ? (relativeOf(node.ganShishen) ?? '—') : '时辰不详'
        }}</span>
      </div>
      <div class="rd-legend" data-testid="legend">
        <div class="rd-legend-title">十神 ↔ 六亲</div>
        <div v-for="item in LEGEND" :key="item.group" class="rd-legend-row">
          <b class="rd-legend-group">{{ item.group }}</b>
          <span class="rd-legend-relative">{{ item.relative }}</span>
          <span v-if="item.genderNote" class="rd-legend-note">{{ item.genderNote }}</span>
        </div>
      </div>
    </div>
    </div>
  </section>
</template>

<style scoped>
.rd {
  overflow-x: auto;
}
.rd-title {
  position: relative;
}
.rd-dy-toggle--title {
  position: absolute;
  right: 0;
  top: 0;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 400;
  color: var(--wx-muted, #666);
  cursor: pointer;
}
.rd-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 12px;
}
.rd-tab {
  flex: 1;
  padding: 6px 0;
  border: none;
  border-radius: 8px;
  background: #f2ede3;
  color: #666;
  font-size: 13px;
  cursor: pointer;
}
.rd-tab--active {
  background: var(--wx-primary-2, #a63431);
  color: #fff;
  font-weight: 600;
}
/* 关系图（纯 CSS 布局，一屏收进） */
.rd-rel {
  position: relative;
  width: 100%;
}
.rd-bazi {
  position: relative;
  display: flex;
  padding: 6px 0;
}
.rd-bazi-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.rd-bazi-hdr {
  font-size: 12px;
  color: var(--wx-muted, #888);
}
.rd-bazi-char {
  font-size: 20px;
  font-weight: 700;
  line-height: 1.2;
}
.rd-bazi-zang {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 2px;
  margin-top: 2px;
}
.rd-bazi-zang-char {
  font-size: 13px;
  font-weight: 600;
}
.rd-edges {
  position: relative;
  width: 100%;
  overflow: visible;
}
.rd-edge {
  position: absolute;
  height: 14px;
  border-top: 1.5px solid currentColor;
  border-left: 1.5px solid currentColor;
  border-right: 1.5px solid currentColor;
  border-radius: 4px 4px 0 0;
}
.rd-edges--bottom .rd-edge {
  border-top: none;
  border-bottom: 1.5px solid currentColor;
  border-radius: 0 0 4px 4px;
}
.rd-edge--合 {
  color: #1b7a3d;
}
.rd-edge--合化 {
  color: #00796b;
}
.rd-edge--六合 {
  color: #558b2f;
}
.rd-edge--三合 {
  color: #2e7d32;
}
.rd-edge--三会 {
  color: #00695c;
}
.rd-edge--冲 {
  color: #c62828;
}
.rd-edge--相冲 {
  color: #ad1457;
}
.rd-edge--刑 {
  color: #e65100;
}
.rd-edge--破 {
  color: #8e24aa;
}
.rd-edge--害 {
  color: #6d4c41;
}
.rd-edge--克 {
  color: #8a5a2b;
}
.rd-edge--生 {
  color: #2e7d32;
}
.rd-edge-tag {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  top: -8px;
  font-size: 11px;
  font-weight: 700;
  background: var(--wx-card, #fff);
  padding: 0 4px;
  color: currentColor;
  white-space: nowrap;
}
.rd-edges--bottom .rd-edge-tag {
  top: auto;
  bottom: -8px;
}
.rd-svg-note {
  font-size: 11px;
  color: var(--wx-muted, #888);
  margin: 8px 0 0;
  text-align: center;
}
.rd-filters,
.rd-filter-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.rd-filter-label {
  font-size: 12px;
  color: var(--wx-muted, #888);
  flex: 0 0 auto;
}
.rd-filter {
  padding: 4px 10px;
  border: 1px solid var(--wx-line, #e4e0d8);
  border-radius: 14px;
  background: #f7f3ea;
  color: #777;
  font-size: 12px;
  cursor: pointer;
}
.rd-filter--active {
  background: var(--wx-primary-2, #a63431);
  border-color: var(--wx-primary-2, #a63431);
  color: #fff;
  font-weight: 600;
}
.rd-rel-summary {
  margin-top: 12px;
  padding: 8px 10px;
  background: #faf6ee;
  border-radius: 10px;
}
.rd-rel-summary-title {
  font-size: 12px;
  color: var(--wx-muted, #888);
  margin-bottom: 4px;
}
.rd-rel-summary-group {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}
.rd-rel-summary-rows {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.rd-rel-summary-row {
  display: flex;
  gap: 8px;
  font-size: 12px;
  line-height: 1.7;
}
.rd-rel-summary-type {
  flex: 0 0 40px;
}
.rd-rel-rejected {
  color: var(--wx-muted);
}
.rd-rel-summary-items {
  color: #555;
}
.rd-grid {
  display: grid;
  grid-template-columns: 1fr 40px 1fr 40px 1fr 40px 1fr;
  row-gap: 6px;
  align-items: center;
}
.rd-flow-pillar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.rd-gz-label {
  font-size: 12px;
  color: var(--wx-muted, #888);
}
.rd-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}
.rd-arrow--sheng {
  color: #2e7d32;
}
.rd-arrow--ke {
  color: #c62828;
}
.rd-arrow--bi {
  color: #888;
}
.rd-arrow-sym {
  font-size: 15px;
}
.rd-flow-note {
  font-size: 11px;
  color: var(--wx-muted, #888);
  margin: 10px 0 0;
}
.rd-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 7px 0;
  font-size: 14px;
  border-bottom: 1px dashed var(--wx-line, #e4e0d8);
}
.rd-row-label {
  flex: 0 0 44px;
  color: var(--wx-muted, #888);
}
.rd-row-value {
  flex: 1;
  font-weight: 600;
  color: var(--wx-primary-2, #a63431);
}
.rd-row-desc {
  flex: 1.2;
  color: #555;
}
.rd-char {
  font-size: 22px;
  font-weight: 700;
  line-height: 1.2;
}
.rd-char--none {
  color: var(--wx-muted, #bbb);
}
.rd-legend {
  margin-top: 12px;
  border-top: 1px dashed var(--wx-line, #e4e0d8);
  padding-top: 8px;
}
.rd-legend-title {
  font-size: 12px;
  color: var(--wx-muted, #888);
  margin-bottom: 4px;
}
.rd-legend-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 12px;
  line-height: 1.7;
}
.rd-legend-group {
  color: var(--wx-primary-2, #a63431);
  flex: 0 0 40px;
}
.rd-legend-note {
  color: var(--wx-muted, #aaa);
}
.rd-warn {
  color: #b8860b;
  font-size: 13px;
  margin: 10px 0 0;
}
/* 极窄屏（<360px）等比缩小，保证四柱不重叠、可读 */
@media (max-width: 360px) {
  .rd-char {
    font-size: 18px;
  }
  .rd-arrow {
    font-size: 11px;
  }
}
</style>
