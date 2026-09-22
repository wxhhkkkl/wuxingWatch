<script setup lang="ts">
/**
 * 命盘板：干上支下 + 十神 + 藏干（012 v2 建立，013 补遗抽为共享组件）。
 *
 * 原局页与岁运两页共用。岁运两页比原局页**多出四个字**（大运、流年两列）——列由
 * `utils/chartColumns.ts` 适配，组件本身不知道「四柱/大运/流年」的区别。
 *
 * 根元素即 `.pillar-row`（**不得再套 wrapper**：原局页的 `.luck-row` 与它是兄弟）。
 * 样式在 `styles/chart.css`。
 */
import type { BoardColumn } from '../utils/chartColumns'
import { ganZhiColor, wxColor } from '../utils/wuxing'

const props = withDefaults(defineProps<{
  columns: BoardColumn[]
  /** 藏干块的 testid 前缀——原局页 `v2`（与 012 期逐字相同），岁运页 `sy-board`。 */
  idPrefix?: string
}>(), { idPrefix: 'v2' })
</script>

<template>
  <div class="pillar-row">
    <div v-for="it in props.columns" :key="it.key" class="pillar-col"
         :class="{ 'is-dim': it.dim }">
      <span class="pillar-label">{{ it.label }}</span>
      <span class="pillar-gan" :style="{ color: wxColor(it.gan_wx) }">{{ it.gan || '—' }}</span>
      <span class="pillar-zhi" :style="{ color: wxColor(it.zhi_wx) }">{{ it.zhi || '—' }}</span>
      <span class="pillar-shishen">{{ it.shishen }}</span>
      <!-- 藏干：该地支所藏天干（干 · 十神），虚线以下；没有明细就整块不画 -->
      <span
        v-if="it.cang_gan.length"
        class="pillar-cang"
        :data-testid="`${props.idPrefix}-canggan-${it.key}`"
      >
        <span v-for="cg in it.cang_gan" :key="cg.gan" class="pillar-cang-row">
          <b :style="{ color: ganZhiColor(cg.gan) }">{{ cg.gan }}</b>
          <i>{{ cg.shishen }}</i>
        </span>
      </span>
    </div>
  </div>
</template>
