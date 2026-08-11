<script setup lang="ts">
import { computed } from 'vue'
import type { DaYunStep, LiuNianStep, Pillar, PillarDetail } from '../types'
import { ganZhiColor } from '../utils/wuxing'

/** 参考"问真八字"布局的 6 列明细表格：流年/大运/年/月/日/时 × 9 个维度行。 */

const props = defineProps<{
  pillars: { year: Pillar | null; month: Pillar | null; day: Pillar | null; time: Pillar | null }
  selectedDayun?: DaYunStep | null
  selectedLiunian?: LiuNianStep | null
}>()

interface Col {
  id: string
  label: string
  gan?: string
  zhi?: string
  detail?: PillarDetail
}

const columns = computed<Col[]>(() => {
  const cols: Col[] = []
  if (props.selectedLiunian?.ganzhi) {
    cols.push({
      id: 'liunian',
      label: '流年',
      gan: props.selectedLiunian.gan,
      zhi: props.selectedLiunian.zhi,
      detail: props.selectedLiunian.detail,
    })
  }
  if (props.selectedDayun?.ganzhi) {
    cols.push({
      id: 'dayun',
      label: '大运',
      gan: props.selectedDayun.gan ?? props.selectedDayun.ganzhi[0],
      zhi: props.selectedDayun.zhi ?? props.selectedDayun.ganzhi[1],
      detail: props.selectedDayun.detail,
    })
  }
  const names = { year: '年柱', month: '月柱', day: '日柱', time: '时柱' } as const
  for (const key of ['year', 'month', 'day', 'time'] as const) {
    const p = props.pillars[key]
    cols.push({ id: key, label: names[key], gan: p?.gan, zhi: p?.zhi, detail: p?.detail })
  }
  return cols
})
</script>

<template>
  <div class="pt-table" :style="{ '--pt-cols': columns.length }">
      <!-- 列表头 -->
      <div class="pt-row pt-head">
        <span class="pt-rowlabel" />
        <span v-for="c in columns" :key="c.id" class="pt-col-header">{{ c.label }}</span>
      </div>

      <!-- 主星 -->
      <div class="pt-row">
        <span class="pt-rowlabel">主星</span>
        <span v-for="c in columns" :key="c.id" class="pt-cell small" :data-testid="`main-${c.id}-star`">
          {{ c.detail?.gan_shishen ?? '—' }}
        </span>
      </div>

      <!-- 天干 / 地支 -->
      <div class="pt-row">
        <span class="pt-rowlabel">天干</span>
        <span
          v-for="c in columns"
          :key="c.id"
          class="pt-cell char"
          :style="{ color: c.gan ? ganZhiColor(c.gan) : 'inherit' }"
          :data-testid="`gan-${c.id}`"
        >
          {{ c.gan ?? '—' }}
        </span>
      </div>
      <div class="pt-row">
        <span class="pt-rowlabel">地支</span>
        <span
          v-for="c in columns"
          :key="c.id"
          class="pt-cell char"
          :style="{ color: c.zhi ? ganZhiColor(c.zhi) : 'inherit' }"
          :data-testid="`zhi-${c.id}`"
        >
          {{ c.zhi ?? '—' }}
        </span>
      </div>

      <!-- 藏干 -->
      <div class="pt-row">
        <span class="pt-rowlabel">藏干</span>
        <span v-for="c in columns" :key="c.id" class="pt-cell small" :data-testid="`main-${c.id}-canggan`">
          <template v-if="c.detail">
            <span
              v-for="cg in c.detail.cang_gan"
              :key="cg.gan"
              class="cg"
              :style="{ color: ganZhiColor(cg.gan) }"
            >
              {{ cg.gan }}<i>{{ cg.shishen }}</i>
            </span>
          </template>
          <template v-else>—</template>
        </span>
      </div>

      <!-- 星运 / 自坐 / 空亡 / 纳音 -->
      <div v-for="row in [
        ['星运', 'xing_yun', 'xingyun'],
        ['自坐', 'zi_zuo', 'zizuo'],
        ['空亡', 'xun_kong', 'xunkong'],
        ['纳音', 'na_yin', 'nayin'],
      ]" :key="row[0]" class="pt-row">
        <span class="pt-rowlabel">{{ row[0] }}</span>
        <span v-for="c in columns" :key="c.id" class="pt-cell small" :data-testid="`main-${c.id}-${row[2]}`">
          {{ c.detail?.[row[1] as keyof PillarDetail] || '—' }}
        </span>
      </div>

      <!-- 神煞（逐个换行） -->
      <div class="pt-row">
        <span class="pt-rowlabel">神煞</span>
        <span v-for="c in columns" :key="c.id" class="pt-cell small shensha" :data-testid="`main-${c.id}-shensha`">
          <template v-if="c.detail?.shen_sha?.length">
            <span v-for="ss in c.detail.shen_sha" :key="ss" class="ss">{{ ss }}</span>
          </template>
          <template v-else>—</template>
        </span>
      </div>
  </div>
</template>

<style scoped>
/* 压缩到一屏内：不横向滚动，列均分宽度 */
.pt-table {
  width: 100%;
}
.pt-row {
  display: grid;
  grid-template-columns: 34px repeat(var(--pt-cols), 1fr);
  align-items: start;
  border-bottom: 1px solid var(--wx-line);
}
.pt-row:last-child {
  border-bottom: none;
}
.pt-head {
  color: var(--wx-muted);
}
.pt-rowlabel {
  font-size: 12px;
  color: var(--wx-muted);
  padding: 6px 0;
}
.pt-col-header {
  font-size: 13px;
  text-align: center;
  padding: 6px 0;
}
.pt-cell {
  text-align: center;
  padding: 6px 0;
  border-left: 1px dashed var(--wx-line);
  min-width: 0;
  word-break: break-all;
}
.pt-cell.char {
  font-size: 22px;
  font-weight: 600;
  line-height: 1.2;
}
.pt-cell.small {
  font-size: 12px;
  color: var(--wx-ink);
}
.pt-cell.shensha {
  color: #8a6d1a;
  line-height: 1.5;
}
.ss {
  display: block;
}
.cg {
  display: block;
  line-height: 1.5;
}
.cg i {
  font-style: normal;
  font-size: 10px;
  color: var(--wx-muted);
  margin-left: 1px;
}
</style>
