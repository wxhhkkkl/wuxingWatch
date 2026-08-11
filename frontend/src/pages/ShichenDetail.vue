<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useChartStore } from '../stores/chart'
import ShichenDial from '../components/ShichenDial.vue'

const router = useRouter()
const chartStore = useChartStore()

const result = computed(() => chartStore.result)
const detail = computed(() => result.value?.shichen ?? null)

const p2 = (n: number) => String(n).padStart(2, '0')

function fmtTime(s: string | null | undefined): string {
  if (!s) return '—'
  const d = new Date(s)
  if (isNaN(d.getTime())) return s
  return `${p2(d.getHours())}:${p2(d.getMinutes())}`
}

function fmtDate(s: string | null | undefined): string {
  if (!s) return '—'
  const d = new Date(s)
  if (isNaN(d.getTime())) return s
  return `${d.getFullYear()}-${p2(d.getMonth() + 1)}-${p2(d.getDate())}`
}

const fmtRange = (a: string, b: string) => `${fmtTime(a)} – ${fmtTime(b)}`

const fmtAlt = (seg: { alt_start: number | null; alt_end: number | null }) =>
  seg.alt_start === null || seg.alt_end === null
    ? '—'
    : `${seg.alt_start.toFixed(1)}°–${seg.alt_end.toFixed(1)}°`

// 四区间：日出→正午 / 正午→日落 / 日落→子夜 / 子夜→次日日出
const intervals = computed(() => {
  const segs = detail.value?.segments
  if (!segs || segs.length !== 24) return []
  const names = ['日出 → 正午', '正午 → 日落', '日落 → 子夜', '子夜 → 次日日出']
  return [0, 6, 12, 18].map((start, k) => ({
    name: names[k],
    range: fmtRange(segs[start].start, start === 18 ? segs[23].end : segs[start + 6].start),
  }))
})

const birthTime = computed(() => result.value?.solar_birth ?? null)
</script>

<template>
  <div class="detail-page">
    <van-nav-bar title="真太阳时 · 时辰详解" left-text="返回" left-arrow @click-left="router.back()" />

    <template v-if="detail">
      <p v-if="!detail.applied" class="banner">当前八字未采用此划分（参考展示）</p>
      <p v-else-if="detail.fallback" class="banner">当日无日出/日落，已采用均分模式</p>

      <!-- 时辰分界表盘 -->
      <section class="wx-card">
        <p class="wx-card-title">当日时辰分界</p>
        <ShichenDial
          :moments="detail.moments"
          :segments="detail.segments"
          :birth-time="birthTime"
          :birth-segment="detail.segment_index"
        />
      </section>

      <!-- 第 1 步：输入参数 -->
      <section class="wx-card">
        <p class="wx-card-title">第 1 步 · 输入参数</p>
        <div class="info-row"><span>出生日期</span>{{ fmtDate(result?.solar_birth) }}</div>
        <div class="info-row"><span>出生时刻</span>{{ fmtTime(result?.solar_birth) }}（当地民用时）</div>
        <div class="info-row"><span>出生地点</span>{{ result?.birth_place || '—' }}</div>
        <div class="info-row"><span>时区</span>{{ result?.timezone || '—' }}</div>
      </section>

      <!-- 第 2 步：太阳关键时刻 -->
      <section class="wx-card">
        <p class="wx-card-title">第 2 步 · 太阳关键时刻</p>
        <div class="info-row"><span>日出</span>{{ fmtTime(detail.moments.sunrise) }}</div>
        <div class="info-row"><span>日落</span>{{ fmtTime(detail.moments.sunset) }}</div>
        <div class="info-row"><span>正午（最高点）</span>{{ fmtTime(detail.moments.solar_noon) }}</div>
        <div class="info-row"><span>子夜（最低点）</span>{{ fmtTime(detail.moments.solar_midnight) }}</div>
      </section>

      <!-- 第 3 步：四区间 -->
      <section class="wx-card">
        <p class="wx-card-title">第 3 步 · 四区间</p>
        <div v-for="iv in intervals" :key="iv.name" class="info-row">
          <span>{{ iv.name }}</span>{{ iv.range }}
        </div>
        <p class="muted">每个区间按太阳高度角等分为 6 段（日出/日落 0° → 正午/子夜最大高度角），全天共 24 段；每 2 段为一个时辰。</p>
      </section>

      <!-- 第 4 步：24 段分界表 -->
      <section class="wx-card">
        <p class="wx-card-title">第 4 步 · 24 段分界（按太阳高度角等分）</p>
        <div class="seg-head">
          <span class="seg-no">#</span>
          <span class="seg-range">起止时刻</span>
          <span class="seg-alt">高度角</span>
          <span class="seg-name">时辰</span>
        </div>
        <div
          v-for="seg in detail.segments"
          :key="seg.index"
          class="seg-row"
          :class="{ 'is-birth': seg.index === detail.segment_index }"
        >
          <span class="seg-no">{{ seg.index + 1 }}</span>
          <span class="seg-range">{{ fmtRange(seg.start, seg.end) }}</span>
          <span class="seg-alt">{{ fmtAlt(seg) }}</span>
          <span class="seg-name">{{ seg.shichen }}时</span>
        </div>
      </section>

      <!-- 第 5 步：归属结论 -->
      <section class="wx-card">
        <p class="wx-card-title">第 5 步 · 归属结论</p>
        <template v-if="detail.segment_index !== null">
          <div class="info-row">
            <span>出生时刻</span>落入第 {{ detail.segment_index + 1 }} 段 →
            <b>{{ detail.shichen }}时</b>
          </div>
          <p v-if="detail.day_offset === 1" class="muted">
            夜子时：出生时刻在子初至太阳子夜之间，按子初换日规则，日柱以次日排。
          </p>
          <p v-if="detail.applied && detail.traditional_shichen" class="muted">
            传统均分法：{{ detail.traditional_shichen }}时
          </p>
        </template>
        <p v-else class="muted">时辰不详：无法判定归属。</p>
      </section>
    </template>

    <van-empty v-else description="暂无时辰数据">
      <van-button type="primary" @click="router.push('/')">去排盘</van-button>
    </van-empty>
  </div>
</template>

<style scoped>
.banner {
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
  flex: 0 0 96px;
}
.seg-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  padding: 4px 8px;
  border-radius: 8px;
}
.seg-row.is-birth {
  background: #faf0e6;
  border: 1px solid var(--wx-primary-2, #a63431);
  font-weight: 600;
}
.seg-no {
  color: var(--wx-muted);
  flex: 0 0 20px;
  text-align: right;
}
.seg-range {
  flex: 1;
  font-variant-numeric: tabular-nums;
}
.seg-alt {
  flex: 0 0 86px;
  text-align: right;
  color: var(--wx-muted);
  font-variant-numeric: tabular-nums;
}
.seg-head {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--wx-muted);
  padding: 4px 8px;
}
.seg-name {
  flex: 0 0 40px;
  text-align: right;
}
.muted {
  color: var(--wx-muted);
  font-size: 13px;
}
</style>
