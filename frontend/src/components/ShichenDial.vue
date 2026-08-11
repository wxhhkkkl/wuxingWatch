<script setup lang="ts">
import { computed } from 'vue'
import type { ShichenMoments, ShichenSegment } from '../types'

const props = defineProps<{
  moments: ShichenMoments
  segments: ShichenSegment[]
  birthTime: string | null
  birthSegment: number | null
}>()

// 表盘几何：viewBox 340，环带 95–130，正午对齐正上方
const SIZE = 340
const C = SIZE / 2
const R_IN = 95
const R_OUT = 130

const windowStart = computed(() => new Date(props.segments[0].start).getTime())
const windowEnd = computed(() => new Date(props.segments[23].end).getTime())

/** 窗口内原始角度（0° = 窗口起点，顺时针） */
function rawAngle(iso: string): number {
  const t = new Date(iso).getTime()
  return ((t - windowStart.value) / (windowEnd.value - windowStart.value)) * 360
}

const noonOffset = computed(() => rawAngle(props.moments.solar_noon) + 90)

/** 显示角度：正午(太阳最高点)转到正上方 */
function displayAngle(iso: string): number {
  return Number((rawAngle(iso) - noonOffset.value).toFixed(4))
}

function polar(r: number, angleDeg: number): [number, number] {
  const rad = (angleDeg * Math.PI) / 180
  return [C + r * Math.cos(rad), C + r * Math.sin(rad)]
}

function sectorPath(a0: number, a1: number): string {
  const [x0, y0] = polar(R_OUT, a0)
  const [x1, y1] = polar(R_OUT, a1)
  const [x2, y2] = polar(R_IN, a1)
  const [x3, y3] = polar(R_IN, a0)
  const large = a1 - a0 > 180 ? 1 : 0
  return `M ${x0} ${y0} A ${R_OUT} ${R_OUT} 0 ${large} 1 ${x1} ${y1} L ${x2} ${y2} A ${R_IN} ${R_IN} 0 ${large} 0 ${x3} ${y3} Z`
}

function isDaytime(seg: ShichenSegment): boolean | null {
  const { sunrise, sunset } = props.moments
  if (!sunrise || !sunset) return null
  const mid = (new Date(seg.start).getTime() + new Date(seg.end).getTime()) / 2
  return new Date(sunrise).getTime() <= mid && mid < new Date(sunset).getTime()
}

const sectors = computed(() =>
  props.segments.map((seg) => {
    const a0 = displayAngle(seg.start)
    const a1 = displayAngle(seg.end)
    const day = isDaytime(seg)
    return {
      index: seg.index,
      d: sectorPath(a0, a1),
      sweep: Number((a1 - a0).toFixed(4)),
      cls: day === null ? '' : day ? 'day' : 'night',
    }
  }),
)

// 12 时辰标签：每个时辰跨两段，标签置于两段分界（段 0/2/4…22 的起点）
const labels = computed(() =>
  Array.from({ length: 12 }, (_, k) => {
    const seg = props.segments[k * 2]
    const [x, y] = polar(80, displayAngle(seg.start))
    return { name: seg.shichen, x, y }
  }),
)

const markers = computed(() => {
  const defs = [
    { key: 'sunrise', label: '日出', time: props.moments.sunrise, cls: 'marker-sunrise' },
    { key: 'noon', label: '正午', time: props.moments.solar_noon, cls: 'marker-noon' },
    { key: 'sunset', label: '日落', time: props.moments.sunset, cls: 'marker-sunset' },
    { key: 'midnight', label: '子夜', time: props.moments.solar_midnight, cls: 'marker-midnight' },
  ]
  return defs
    .filter((m) => m.time)
    .map((m) => {
      const a = displayAngle(m.time as string)
      const [x1, y1] = polar(R_OUT + 3, a)
      const [x2, y2] = polar(R_OUT + 12, a)
      const [tx, ty] = polar(R_OUT + 26, a)
      return { ...m, x1, y1, x2, y2, tx, ty }
    })
})

const birthAngle = computed(() => (props.birthTime ? displayAngle(props.birthTime) : null))
const birthShichen = computed(() =>
  props.birthSegment !== null ? props.segments[props.birthSegment]?.shichen : null,
)
</script>

<template>
  <div class="dial-wrap">
    <svg :viewBox="`0 0 ${SIZE} ${SIZE}`" class="dial" role="img" aria-label="当日时辰分界表盘">
      <!-- 24 段扇区 -->
      <path
        v-for="s in sectors"
        :key="s.index"
        class="seg-sector"
        :class="[s.cls, { 'birth-sector': s.index === birthSegment }]"
        :d="s.d"
        :data-sweep="s.sweep"
      />

      <!-- 12 时辰标签 -->
      <text
        v-for="l in labels"
        :key="l.name"
        class="shichen-label"
        :x="l.x"
        :y="l.y"
        text-anchor="middle"
        dominant-baseline="central"
      >
        {{ l.name }}
      </text>

      <!-- 关键时刻标记 -->
      <g v-for="m in markers" :key="m.key" :class="m.cls">
        <line :x1="m.x1" :y1="m.y1" :x2="m.x2" :y2="m.y2" class="marker-line" />
        <text :x="m.tx" :y="m.ty" class="marker-label" text-anchor="middle" dominant-baseline="central">
          {{ m.label }}
        </text>
      </g>

      <!-- 出生时刻指针 -->
      <line
        v-if="birthAngle !== null"
        class="birth-pointer"
        :x1="C"
        :y1="C"
        :x2="C"
        :y2="C - R_OUT - 6"
        :transform="`rotate(${birthAngle} ${C} ${C})`"
      />

      <!-- 中心归属时辰 -->
      <text v-if="birthShichen" :x="C" :y="C - 8" class="center-shichen" text-anchor="middle">
        {{ birthShichen }}时
      </text>
    </svg>
  </div>
</template>

<style scoped>
.dial-wrap {
  display: flex;
  justify-content: center;
}
.dial {
  width: 100%;
  max-width: 340px;
  height: auto;
}
.seg-sector {
  fill: #f2ede2;
  stroke: #fff;
  stroke-width: 1;
}
.seg-sector.day {
  fill: #f7e3b0;
}
.seg-sector.night {
  fill: #cfd9ea;
}
.seg-sector.birth-sector {
  fill: #e8b4a0;
  stroke: #a63431;
}
.shichen-label {
  font-size: 13px;
  fill: var(--wx-ink, #333);
}
.marker-line {
  stroke: #a63431;
  stroke-width: 2;
}
.marker-label {
  font-size: 11px;
  fill: var(--wx-muted, #888);
}
.birth-pointer {
  stroke: #a63431;
  stroke-width: 2.5;
  stroke-linecap: round;
}
.center-shichen {
  font-size: 22px;
  font-weight: 600;
  fill: var(--wx-primary-2, #a63431);
}
</style>
