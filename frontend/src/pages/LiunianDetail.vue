<script setup lang="ts">
/**
 * 013 期：「**加入流年**」页（US3 / FR-021c）。
 *
 * 三阶段模型的第 3 页——「大运阶段」与「流年阶段」的判断**并列罗列**（FR-016c /
 * SC-009），每项**各自标明来源阶段**（FR-024 / SC-008），使使用者一眼看出
 * 「加流年之后哪几项变了、分别变成什么」。
 *
 * **引擎不合成吉凶**（FR-016a）：本页只做同名项的成对对照，不出吉凶档位、
 * 不给事件断语——判断留给使用者。
 *
 * 结论**按需实时算、不落库**（FR-026）；入口两处同「加入大运」页（FR-021a）。
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSuiyun } from '../utils/suiyun'
import PillarBoard from '../components/PillarBoard.vue'
import SuiyunStage from '../components/SuiyunStage.vue'
import type { V2Pair } from '../types'

const router = useRouter()
const { chart, steps, selectedIndex, years, selectedYear, boardColumns, blocked,
        degradeReason, notes, sourceError, noChart, conclusion, loading, error } =
  useSuiyun({ withLiunian: true })

const hasBoard = computed(() => boardColumns.value.some((c) => c.key === 'year'))

const GEJU_LABEL: Record<string, string> = {
  zheng: '正格', cong_ruo: '从弱格', cong_qiang: '从强格', cong_yin: '从印格',
  cong_sha: '从杀格', cong_cai: '从财格', hua: '化格',
}

/** 成对项的值可能是标量、数组或对象（调候/层次）——统一成一行可读文本。 */
function fmt(key: string, v: unknown): string {
  if (v === null || v === undefined) return '—'
  if (key === 'ge_ju.type') return GEJU_LABEL[String(v)] ?? String(v)
  if (Array.isArray(v)) return v.length ? v.join('、') : '—'
  if (typeof v === 'object') {
    const o = v as Record<string, unknown>
    if (key === 'tiaohou') {
      return [o.element ?? '无需调候', o.quantified].filter(Boolean).join(' · ') || '—'
    }
    if (key === 'layers') return String(o.verdict || o.basis || '—')
    return JSON.stringify(v)
  }
  return String(v)
}

const pairs = computed<V2Pair[]>(() => conclusion.value?.pairs ?? [])
</script>

<template>
  <div class="detail-page">
    <van-nav-bar title="岁运推导 · 加入流年" left-text="返回" left-arrow @click-left="router.back()" />

    <!-- 命盘：大运、流年两列居左（与原局页同一张卡、同一份实现） -->
    <section v-if="hasBoard" class="wx-card">
      <p class="wx-card-title">命盘</p>
      <PillarBoard :columns="boardColumns" id-prefix="sy-board" />
    </section>

    <van-empty v-if="noChart" data-testid="sy-empty" description="暂无可推导的命盘（旧记录可重新排盘获取）">
      <van-button type="primary" @click="router.push('/')">去排盘</van-button>
    </van-empty>

    <p v-else-if="sourceError" class="warn-line">{{ sourceError }}</p>

    <!-- 降级（FR-025）：尚未起运 / 四柱输入定不出年份 -->
    <van-empty v-else-if="blocked" data-testid="sy-degrade" :description="degradeReason">
      <van-button type="primary" @click="router.back()">返回</van-button>
    </van-empty>

    <template v-else>
      <section class="wx-card">
        <p class="wx-card-title">选择大运与流年</p>
        <div class="pick-row">
          <label class="pick-label" for="sy-dayun">大运</label>
          <select id="sy-dayun" v-model.number="selectedIndex"
                  class="pick-select" data-testid="sy-dayun-select">
            <option v-for="(s, i) in steps" :key="s.ganzhi" :value="i">
              {{ s.ganzhi }}{{ s.start_year ? `（${s.start_year} 年起）` : '' }}
            </option>
          </select>
        </div>
        <div class="pick-row">
          <label class="pick-label" for="sy-year">流年</label>
          <select id="sy-year" v-model.number="selectedYear"
                  class="pick-select" data-testid="sy-year-select">
            <option v-for="y in years" :key="y" :value="y">{{ y }} 年</option>
          </select>
        </div>
        <p v-if="notes.length" class="warn-line">{{ notes.join('；') }}</p>
        <p v-for="(d, i) in conclusion?.degradations ?? []" :key="i" class="warn-line">
          ⚠️ {{ d }}
        </p>
      </section>

      <p class="stage-line" data-testid="sy-stage">阶段 3 · 加入流年</p>

      <van-loading v-if="loading" class="loading" />
      <p v-else-if="error" class="warn-line">{{ error }}</p>

      <template v-else-if="conclusion">
        <!-- 两阶段同名判断**成对列出**（FR-016c / SC-009）——每侧各标来源阶段（FR-024） -->
        <section v-if="pairs.length" class="wx-card">
          <p class="wx-card-title">两阶段对照</p>
          <p class="pair-note">
            下列同名判断按「该步大运」与「该年流年」并列，各自标明所属阶段；
            <b>引擎不合成吉凶</b>，如何取舍由使用者判断。
          </p>
          <div class="pair-table">
            <div v-for="p in pairs" :key="p.key" class="pair-row"
                 :class="{ 'is-changed': p.changed }"
                 :data-testid="`sy-pair-${p.key}`">
              <span class="pair-label">{{ p.label }}</span>
              <span class="pair-cell" :data-testid="`sy-pair-${p.key}-dayun`">
                <em class="src src-dayun">属大运</em>{{ fmt(p.key, p.dayun.value) }}
              </span>
              <span class="pair-cell" :data-testid="`sy-pair-${p.key}-liunian`">
                <em class="src src-liunian">属流年</em>{{ fmt(p.key, p.liunian.value) }}
              </span>
            </div>
          </div>
        </section>

        <SuiyunStage v-if="conclusion.dayun" phase="dayun" :step="conclusion.dayun" />
        <SuiyunStage v-if="conclusion.liunian" phase="liunian" :step="conclusion.liunian" />
      </template>
    </template>
  </div>
</template>

<style scoped>
.loading {
  margin: 30px auto;
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
.stage-line {
  margin: 12px 14px 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--wx-muted);
}
.pick-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
}
.pick-label {
  font-size: 12px;
  color: var(--wx-muted);
}
.pick-select {
  flex: 1;
  font-size: 14px;
  padding: 7px 8px;
  border: 1px solid var(--wx-line);
  border-radius: 8px;
  background: #fff;
  color: var(--wx-ink);
}
/* 命盘卡的柱列样式见 `styles/chart.css`（013 补遗起与**原局页共用一份**）。
   本页不再自带 `.pillar-*` 副本——残留的那份会通过组件**根元素**继续命中，
   凭空多出上边距。 */
.pair-note {
  margin: 4px 0 8px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--wx-muted);
}
.pair-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 6px;
  border-radius: 8px;
  font-size: 12.5px;
}
.pair-row.is-changed {
  background: #fbf5e8;
}
.pair-label {
  flex: 0 0 4.5em;
  color: var(--wx-muted);
}
.pair-cell {
  flex: 1;
  min-width: 0;
  line-height: 1.5;
}
.src {
  display: inline-block;
  margin-right: 5px;
  padding: 0 5px;
  border-radius: 5px;
  font-size: 10.5px;
  font-style: normal;
  color: #fff;
}
.src-dayun { background: #8a6a3a; }
.src-liunian { background: #2d5f8a; }
</style>
