<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { DaYunStep, LiuRiItem, LiuShiItem, LiuYueItem } from '../types'
import { ganZhiColor } from '../utils/wuxing'

/** 大运/流年/流月/流日/流时联动横条：逐级点击下钻，下级列表由父组件按需加载。 */

const props = defineProps<{
  steps: DaYunStep[]
  selectedDayunIndex: number
  selectedLiunianYear: number | null
  startAge?: number | null
  startMonth?: number | null
  startDay?: number | null
  startHour?: number | null
  jiaoYun?: { year_gan: string; jie: string; days: number; hours: number; first_year: number } | null
  birthYear?: number | null
  liuyue?: LiuYueItem[]
  selectedLiuyueBranch?: string | null
  liuri?: LiuRiItem[]
  selectedLiuriDate?: string | null
  liushi?: LiuShiItem[]
  selectedLiushiZhi?: string | null
  loadingLevel?: 'month' | 'day' | 'hour' | null
}>()

const emit = defineEmits<{
  'select-dayun': [index: number]
  'select-liunian': [year: number]
  'select-liuyue': [branch: string]
  'select-liuri': [date: string]
  'select-liushi': [zhi: string]
}>()

const selectedStep = computed(() => props.steps[props.selectedDayunIndex] ?? null)
const liunianList = computed(() => selectedStep.value?.liu_nian ?? [])

const currentYear = new Date().getFullYear()
const currentAgeXu = computed(() =>
  props.birthYear ? currentYear - props.birthYear + 1 : null,
)

const todayStr = (() => {
  const d = new Date()
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
})()

const root = ref<HTMLElement | null>(null)

// 自动选中的下钻项可能溢出可视区（流日约 30 项），滚动到选中处
watch(
  () => [props.liuyue, props.liuri, props.liushi],
  async () => {
    await nextTick()
    root.value
      ?.querySelector('.fs-liuyue-item.active, .fs-liuri-item.active, .fs-liushi-item.active')
      ?.scrollIntoView?.({ inline: 'center', block: 'nearest' })
  },
)
</script>

<template>
  <div ref="root" class="fs">
    <div v-if="startAge != null && birthYear" class="fs-qiyun">
      <span>
        出生后 {{ startAge }} 年 {{ startMonth ?? 0 }} 月<template v-if="startDay != null"> {{ startDay }} 天 {{ startHour ?? 0 }} 时</template>起运
      </span>
      <span v-if="currentAgeXu" class="fs-age">{{ currentAgeXu }}岁</span>
    </div>
    <div v-if="jiaoYun" class="fs-qiyun fs-jiaoyun">
      <span>
        交运：逢{{ jiaoYun.year_gan }}年 {{ jiaoYun.jie }}后{{ jiaoYun.days }}天{{ jiaoYun.hours }}小时交大运
      </span>
    </div>

    <!-- 大运横条 -->
    <div class="fs-strip">
      <div
        v-for="(s, i) in steps"
        :key="s.ganzhi + i"
        class="fs-dayun-item"
        :class="{ active: i === selectedDayunIndex }"
        @click="emit('select-dayun', i)"
      >
        <small v-if="s.start_year" class="fs-year">{{ s.start_year }}</small>
        <small v-if="s.start_age_xu" class="fs-age-xu">{{ s.start_age_xu }}岁</small>
        <span class="fs-gz">
          <b :style="{ color: ganZhiColor(s.gan ?? s.ganzhi[0]) }">{{ s.gan ?? s.ganzhi[0] }}</b>
          <b :style="{ color: ganZhiColor(s.zhi ?? s.ganzhi[1]) }">{{ s.zhi ?? s.ganzhi[1] }}</b>
        </span>
        <small v-if="s.gan_shishen" class="fs-ss">{{ s.gan_shishen }}</small>
      </div>
    </div>

    <!-- 流年横条 -->
    <div v-if="liunianList.length" class="fs-strip liunian">
      <div
        v-for="n in liunianList"
        :key="n.year"
        class="fs-liunian-item"
        :class="{ active: n.year === selectedLiunianYear, current: n.year === currentYear }"
        @click="emit('select-liunian', n.year)"
      >
        <small class="fs-year">{{ n.year }}</small>
        <span class="fs-gz">
          <b :style="{ color: ganZhiColor(n.gan) }">{{ n.gan }}</b>
          <b :style="{ color: ganZhiColor(n.zhi) }">{{ n.zhi }}</b>
        </span>
        <small class="fs-ss">{{ n.gan_shishen }}</small>
      </div>
    </div>

    <!-- 流月横条 -->
    <div v-if="loadingLevel === 'month'" class="fs-loading">流月加载中…</div>
    <div v-else-if="liuyue?.length" class="fs-strip liunian">
      <div
        v-for="m in liuyue"
        :key="m.branch"
        class="fs-liunian-item fs-liuyue-item"
        :class="{ active: m.branch === selectedLiuyueBranch }"
        @click="emit('select-liuyue', m.branch)"
      >
        <small class="fs-year">{{ m.label }}</small>
        <span class="fs-gz">
          <b :style="{ color: ganZhiColor(m.gan) }">{{ m.gan }}</b>
          <b :style="{ color: ganZhiColor(m.zhi) }">{{ m.zhi }}</b>
        </span>
        <small class="fs-ss">{{ m.gan_shishen }}</small>
      </div>
    </div>

    <!-- 流日横条 -->
    <div v-if="loadingLevel === 'day'" class="fs-loading">流日加载中…</div>
    <div v-else-if="liuri?.length" class="fs-strip liunian">
      <div
        v-for="d in liuri"
        :key="d.date"
        class="fs-liunian-item fs-liuri-item"
        :class="{ active: d.date === selectedLiuriDate, current: d.date === todayStr }"
        @click="emit('select-liuri', d.date)"
      >
        <small class="fs-year">{{ d.date.slice(5).replace('-', '.') }}</small>
        <span class="fs-gz">
          <b :style="{ color: ganZhiColor(d.gan) }">{{ d.gan }}</b>
          <b :style="{ color: ganZhiColor(d.zhi) }">{{ d.zhi }}</b>
        </span>
        <small class="fs-ss">{{ d.gan_shishen }}</small>
      </div>
    </div>

    <!-- 流时横条 -->
    <div v-if="loadingLevel === 'hour'" class="fs-loading">流时加载中…</div>
    <div v-else-if="liushi?.length" class="fs-strip liunian">
      <div
        v-for="h in liushi"
        :key="h.zhi"
        class="fs-liunian-item fs-liushi-item"
        :class="{ active: h.zhi === selectedLiushiZhi }"
        @click="emit('select-liushi', h.zhi)"
      >
        <small class="fs-year">{{ h.zhi }}时</small>
        <span class="fs-gz">
          <b :style="{ color: ganZhiColor(h.ganzhi[0]) }">{{ h.ganzhi[0] }}</b>
          <b :style="{ color: ganZhiColor(h.ganzhi[1]) }">{{ h.ganzhi[1] }}</b>
        </span>
        <small class="fs-ss">{{ h.gan_shishen }}</small>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fs-qiyun {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--wx-ink);
  margin-bottom: 8px;
}
.fs-age {
  color: var(--wx-muted);
}
.fs-jiaoyun {
  color: var(--wx-muted);
  font-size: 12px;
  margin-top: -4px;
}
.fs-strip {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 4px;
}
.fs-strip.liunian {
  margin-top: 8px;
  border-top: 1px dashed var(--wx-line);
  padding-top: 8px;
}
.fs-dayun-item,
.fs-liunian-item {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
  padding: 6px 8px;
  border: 1px solid var(--wx-line);
  border-radius: 10px;
  background: #faf6ee;
  cursor: pointer;
  min-width: 52px;
}
.fs-dayun-item.active,
.fs-liunian-item.active {
  border-color: var(--wx-primary-2, #a63431);
  background: #f7ece7;
}
.fs-liunian-item.current .fs-year {
  color: var(--wx-primary-2, #a63431);
  font-weight: 700;
}
.fs-year {
  font-size: 10px;
  color: var(--wx-muted);
}
.fs-loading {
  margin-top: 8px;
  border-top: 1px dashed var(--wx-line);
  padding: 10px 4px 6px;
  font-size: 12px;
  color: var(--wx-muted);
}
.fs-age-xu {
  font-size: 10px;
  color: var(--wx-muted);
}
.fs-gz {
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.15;
}
.fs-gz b {
  font-size: 17px;
}
.fs-ss {
  font-size: 10px;
  color: var(--wx-muted);
}
</style>
