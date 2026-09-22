<script setup lang="ts">
/**
 * 判定依据里的**逐段命盘快照**（012 v2 建立，013 补遗抽为共享组件）。
 *
 * 原局页与岁运两页共用同一份实现——「效果保持一致」不靠两份代码对齐，靠只有一份。
 * 根元素即 `.step-chart`（**不得再套 wrapper**：既有测试断言的是 `<li>` 的**直接子节点**
 * 下标，多一层就会打破「速览格紧邻命盘」「逐实例快照插在对应算式之后」两条）。
 *
 * 岁运两页比原局页**多出四个字**（大运、流年两列，居左）：
 * 后端把这两列**追加在原局四柱之后**（为的是让 `ban`／`ban_cheng` 的扩展下标对齐），
 * 显示顺序由本组件重排——故列序这条规则只有这一处。
 */
import { computed } from 'vue'
import type { V2ChartPillar } from '../types'
import { ganZhiColor, wxColor } from '../utils/wuxing'

const props = withDefaults(defineProps<{
  /** 后端给的列（原局 4 列；岁运路径另含 `_dayun` / `_liunian`）。 */
  pillars: V2ChartPillar[]
  /** 快照标题（如「本段结束时的命盘」）。 */
  label?: string
  /** 根元素的 testid。 */
  testid: string
  /** 列级 testid 前缀——原局页 `v2`（与 012 期逐字相同），岁运页传 `sy-<阶段>`。 */
  idPrefix?: string
  /** 该阶段**未参与**的字：后端不建这一列时补一个灰显占位（如阶段 2 的流年）。 */
  placeholders?: { key: string; label: string }[]
  /** 口径说明（如「岁运之支藏干为平加项」）。 */
  note?: string
}>(), { label: '', idPrefix: 'v2', placeholders: () => [], note: '' })

/** 岁运两列的固定次序与**最左**位置（与命盘图 RelationDiagram 的列序一致）。 */
const SY_KEYS = ['_dayun', '_liunian'] as const

/** 藏干「字变」标记 → 样式类（标记值是中文，不能直接当类名）。 */
const CHANGE_CLASS: Record<string, string> = {
  新增: 'is-new', 归零: 'is-zero', 增力: 'is-up', 减力: 'is-down', 变纯: 'is-pure',
}

interface DisplayCol {
  key: string
  label: string
  /** 缺列时的灰显占位——没有这一列，就没有它的度数。 */
  pillar: V2ChartPillar | null
}

const columns = computed<DisplayCol[]>(() => {
  const byKey = new Map(props.pillars.map((p) => [p.key, p]))
  const wanted = new Set(props.placeholders.map((p) => p.key))
  const lead: DisplayCol[] = []
  for (const k of SY_KEYS) {
    const p = byKey.get(k)
    if (p) {
      lead.push({ key: k, label: p.label, pillar: p })
      byKey.delete(k)
    } else if (wanted.has(k)) {
      lead.push({ key: k, label: props.placeholders.find((x) => x.key === k)!.label,
                  pillar: null })
    }
  }
  const rest = props.pillars
    .filter((p) => byKey.has(p.key))
    .map((p) => ({ key: p.key, label: p.label, pillar: p }))
  return [...lead, ...rest]
})

const tid = (suffix: string, key: string) => `${props.idPrefix}-${suffix}-${key}`
</script>

<template>
  <div class="step-chart" :data-testid="testid">
    <p v-if="label" class="step-chart-caption">{{ label }}</p>
    <!-- 6 列时收一档间距；原局 4 列不受影响 -->
    <div class="pillar-row pillar-mini" :class="{ 'is-dense': columns.length > 4 }">
      <div v-for="c in columns" :key="c.key" class="pillar-col"
           :class="{ 'is-dim': !c.pillar }" :data-testid="tid('chart', c.key)">
        <span class="pillar-label">{{ c.label }}</span>

        <!-- 占位列：本阶段这个字根本没上场（如阶段 2 的流年），只有位置没有度数 -->
        <template v-if="!c.pillar">
          <span class="pillar-gan">—</span>
          <span class="pillar-zhi">—</span>
        </template>

        <template v-else>
          <span class="pillar-gan"
                :style="{ color: ganZhiColor(c.pillar.gan_original ?? c.pillar.gan) }">
            <!-- 天干五合合化成功会**换字**（甲→戊，书 上 1593），但显示上**不改字**：
                 正字仍是原局那个字，另用**化神五行的框 + 底色**标出已合化，
                 换字后的字放下面小字。合而不化只减力、不换字（书 上 1595）。 -->
            <span v-if="c.pillar.gan_original" class="gan-hua"
                  :data-testid="tid('gan-hua', c.key)"
                  :style="{ borderColor: wxColor(c.pillar.gan_wx),
                            background: `color-mix(in srgb, ${wxColor(c.pillar.gan_wx)} 15%, transparent)` }"
            >{{ c.pillar.gan_original }}</span>
            <template v-else>{{ c.pillar.gan }}</template><i class="pillar-deg">{{ c.pillar.gan_degree }}</i>
          </span>
          <span v-if="c.pillar.gan_original" class="pillar-sub pillar-changed"
                :data-testid="tid('gan-changed', c.key)">
            {{ c.pillar.gan_change }}→{{ c.pillar.gan }}
          </span>
          <span v-else-if="c.pillar.gan_change" class="pillar-sub"
                :data-testid="tid('gan-changed', c.key)">{{ c.pillar.gan_change }}</span>
          <!-- 第 5 段起：主数（组旺度）之外，再给出「自身」「根」两个分量，
               三者恒有 主数 = 自身 + 根；第 7 段逐实例快照里都会随结算变。
               **岁运之干恒不给这两个分量**——那两字在宣示该等式成立，对它不成立。 -->
          <span v-if="c.pillar.gan_own !== null && c.pillar.gan_own !== undefined"
                class="pillar-sub" :data-testid="tid('gan-own', c.key)">
            自身 {{ c.pillar.gan_own }}
          </span>
          <span class="pillar-zhi" :style="{ color: wxColor(c.pillar.zhi_effective_wx) }">
            <!-- 支被合化改宗时字也不换，套**生效五行**的框 + 底色（与天干换字同一套视觉） -->
            <span v-if="c.pillar.zhi_effective_wx !== c.pillar.zhi_wx" class="gan-hua"
                  :data-testid="tid('zhi-hua', c.key)"
                  :style="{ borderColor: wxColor(c.pillar.zhi_effective_wx),
                            background: `color-mix(in srgb, ${wxColor(c.pillar.zhi_effective_wx)} 15%, transparent)` }"
            >{{ c.pillar.zhi }}</span>
            <template v-else>{{ c.pillar.zhi }}</template><i
                v-if="c.pillar.zhi_effective_wx !== c.pillar.zhi_wx"
                class="pillar-sub pillar-changed">变{{ c.pillar.zhi_effective_wx }}</i>
          </span>
          <span class="pillar-cang">
            <span v-for="h in c.pillar.hidden" :key="h.gan" class="pillar-cang-row"
                  :class="{ 'is-off': h.change === '归零' }"
                  :data-testid="tid('chart-hidden', c.key)">
              <b :style="{ color: ganZhiColor(h.gan) }">{{ h.gan }}</b>
              <i class="cang-deg">{{ h.degree }}</i>
              <i v-if="h.change" class="cang-mark" :class="CHANGE_CLASS[h.change]">{{ h.change }}</i>
            </span>
          </span>
        </template>
      </div>
    </div>
    <p v-if="note" class="step-chart-note">{{ note }}</p>
  </div>
</template>
