<script setup lang="ts">
import { computed } from 'vue'
import type { DaYunStep } from '../types'
import { ganZhiColor } from '../utils/wuxing'

/** 大运/流年联动横条：点击大运切换流年列表，点击流年选中。 */

const props = defineProps<{
  steps: DaYunStep[]
  selectedDayunIndex: number
  selectedLiunianYear: number | null
  startAge?: number | null
  startMonth?: number | null
  birthYear?: number | null
}>()

const emit = defineEmits<{
  'select-dayun': [index: number]
  'select-liunian': [year: number]
}>()

const selectedStep = computed(() => props.steps[props.selectedDayunIndex] ?? null)
const liunianList = computed(() => selectedStep.value?.liu_nian ?? [])

const currentYear = new Date().getFullYear()
const currentAgeXu = computed(() =>
  props.birthYear ? currentYear - props.birthYear + 1 : null,
)
</script>

<template>
  <div class="fs">
    <div v-if="startAge != null && birthYear" class="fs-qiyun">
      <span>出生后 {{ startAge }} 年 {{ startMonth ?? 0 }} 月起运</span>
      <span v-if="currentAgeXu" class="fs-age">{{ currentAgeXu }}岁</span>
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
