<script setup lang="ts">
/**
 * 014 期：**大运引擎2** 页（US1 / US2）。
 *
 * 按教师七步流程（＋ R30 的天干五合）**独立**算出的另一套大运旺度——**与现引擎并存**，不并排、不打差异标记
 * （裁定④）。页面自上而下：选大运 → 逐步依据 → **静态 / 动态 / 日主**三张汇总
 * （静动两张各含五行合计与实例两段，实例明细不再单列一块）。
 *
 * 结果**按需实时算、不落库**（FR-008）。页面上 MUST 标明这是**引擎2** 的数。
 * 入口：结果页与记录详情页各一个（FR-006），`?record=<id>` 时从记录进入。
 *
 * 页首是该盘的**八字 ＋ 当前选中那一步大运**（`PillarBoard`，与岁运两页同一份实现）——
 * 只摆字、不带度数，引擎2 的数仍在下面三层里。
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDayun2 } from '../utils/dayun2'
import { wxColor } from '../utils/wuxing'
import FortuneStrip from '../components/FortuneStrip.vue'
import PillarBoard from '../components/PillarBoard.vue'
import StepList from '../components/StepList.vue'

const router = useRouter()
const {
  chart, steps, selectedIndex, selectStep, current, elementRows, boardColumns, conclusion,
  loading, error, sourceError, noChart, blocked,
} = useDayun2()

const hasBoard = computed(() => boardColumns.value.some((c) => c.key === 'year'))

/** 起运信息与交运说明（与现局页同一份口径，取自同一张命盘）。 */
const dayun = computed(() => chart.value?.da_yun ?? null)
const birthYear = computed(() =>
  chart.value?.solar_birth ? new Date(chart.value.solar_birth).getFullYear() : null,
)

/** 大运增量一行——`木 +0 · 火 -1 …`（0 也照写，省得空下来像漏了一行）。 */
const deltaText = computed(() =>
  elementRows.value.map((r) => `${r.wx} ${r.delta > 0 ? `+${r.delta}` : r.delta}`).join(' · '),
)
</script>

<template>
  <div class="detail-page">
    <van-nav-bar title="大运引擎2" left-text="返回" left-arrow @click-left="router.back()" />

    <!-- 这一张盘的八字 ＋ 当前选中那一步大运（大运居左，与岁运两页同一张卡、同一份实现）。
         放在最前：下面的依据与汇总算的是同一个人的盘，先看见盘再读数。命盘只画四个字，
         引擎2 的数不混进来（FR-007）。 -->
    <section v-if="hasBoard" class="wx-card" data-testid="d2-board">
      <p class="wx-card-title">命盘（八字 · 大运）</p>
      <PillarBoard :columns="boardColumns" id-prefix="d2-board" />
    </section>

    <van-empty v-if="noChart" data-testid="d2-empty"
               description="暂无可推导的命盘（旧记录可重新排盘获取）">
      <van-button type="primary" @click="router.push('/')">去排盘</van-button>
    </van-empty>

    <p v-else-if="sourceError" class="warn-line">{{ sourceError }}</p>

    <van-empty v-else-if="blocked" data-testid="d2-degrade"
               description="该盘没有可用的大运步（尚未起运），无法给出引擎2 的结果">
      <van-button type="primary" @click="router.back()">返回</van-button>
    </van-empty>

    <template v-else>
      <!-- 选择大运：用与现局页**同一份**横条（`FortuneStrip`），不另造一套选步控件。
           `dayun-only`——本页只按大运步取数，没有流年那一维。 -->
      <section class="wx-card" data-testid="d2-picker">
        <p class="wx-card-title">
          选择大运
          <span class="engine-badge" data-testid="d2-engine-tag">引擎2</span>
        </p>
        <FortuneStrip
          :steps="steps"
          :selected-dayun-index="selectedIndex"
          :start-age="dayun?.start_age"
          :start-month="dayun?.start_month"
          :start-day="dayun?.start_day"
          :start-hour="dayun?.start_hour"
          :jiao-yun="dayun?.jiao_yun ?? null"
          :birth-year="birthYear"
          dayun-only
          @select-dayun="selectStep"
        />
        <p v-for="(d, i) in conclusion?.degradations ?? []" :key="i" class="warn-line">
          ⚠️ {{ d }}
        </p>
      </section>

      <van-loading v-if="loading" class="loading" />
      <p v-else-if="error" class="warn-line">{{ error }}</p>

      <template v-else-if="current">
        <!-- 逐步依据——**与现局页同一套渲染**：序号徽章标题、算式行（对象/算式/数值）、
             五行速览格、结果行、段末五柱快照。共用 `StepList` 是为了「观感一致」不靠
             两份代码对齐，靠只有一份（同 StepChart 的既有理由）。 -->
        <section class="wx-card">
          <p class="wx-card-title">逐步依据</p>
          <StepList :steps="current.phases" id-prefix="d2" :trace-target-color="true" />
        </section>

        <!-- 三块汇总排在全页最后：静态一张、动态一张（各含五行合计与实例两段），日主一张。
             五行合计用与段末速览**同一套格子**（`.step-scores`，见 styles/chart.css），
             免得同一页里两处速览长得不一样。 -->
        <section class="wx-card" data-testid="d2-static-sum">
          <p class="wx-card-title">静态旺度汇总</p>
          <p class="sum-head">五行合计</p>
          <div class="step-scores">
            <div v-for="r in elementRows" :key="r.wx" class="score-cell" :data-wx="r.wx">
              <span class="score-wx step-score-wx" :style="{ color: wxColor(r.wx) }">{{ r.wx }}</span>
              <span class="score-val">{{ r.static }}</span>
            </div>
          </div>
          <p class="sum-note">大运增量：{{ deltaText }}</p>
          <p class="sum-head">实例</p>
          <table class="d2-table" data-testid="d2-static-instances">
            <thead><tr><th>实例</th><th>五行</th><th>静态</th></tr></thead>
            <tbody>
              <tr v-for="i in current.instances" :key="i.key" :data-kind="i.kind">
                <td>{{ i.label }}</td><td>{{ i.wx }}</td><td>{{ i.static }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section class="wx-card" data-testid="d2-dynamic-sum">
          <p class="wx-card-title">动态旺度汇总</p>
          <p class="sum-head">五行合计</p>
          <div class="step-scores">
            <div v-for="r in elementRows" :key="r.wx" class="score-cell" :data-wx="r.wx">
              <span class="score-wx step-score-wx" :style="{ color: wxColor(r.wx) }">{{ r.wx }}</span>
              <span class="score-val">{{ r.dynamic }}</span>
            </div>
          </div>
          <p class="sum-head">实例</p>
          <table class="d2-table" data-testid="d2-dynamic-instances">
            <thead><tr><th>实例</th><th>五行</th><th>动态</th></tr></thead>
            <tbody>
              <tr v-for="i in current.instances" :key="i.key" :data-kind="i.kind">
                <td>{{ i.label }}</td><td>{{ i.wx }}</td><td>{{ i.dynamic }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section class="wx-card" data-testid="d2-day-master-sum">
          <p class="wx-card-title">日主旺度汇总</p>
          <p class="sum-head">{{ current.day_master.members.join('、') }}（{{ current.day_master.wx }}）</p>
          <div class="step-scores" data-testid="d2-day-master">
            <div class="score-cell">
              <span class="score-wx step-score-wx">静态</span>
              <span class="score-val">{{ current.day_master.static }}</span>
            </div>
            <div class="score-cell">
              <span class="score-wx step-score-wx">动态</span>
              <span class="score-val">{{ current.day_master.dynamic }}</span>
            </div>
            <div class="score-cell">
              <span class="score-wx step-score-wx">档位</span>
              <span class="score-val">{{ current.day_master.level }}</span>
            </div>
          </div>
        </section>
      </template>
    </template>
  </div>
</template>

<style scoped>
/* 表格是本页自己的（汇总里的实例）；逐步依据与五行速览格走共享样式（styles/chart.css） */
.d2-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.d2-table th, .d2-table td { padding: 6px 4px; border-bottom: 1px solid var(--wx-line, #eee); text-align: left; }
/* 汇总块内的小标题（「五行合计」「实例」）与增量那行 */
.sum-head { margin: 8px 0 0; font-size: 12px; color: var(--wx-muted); }
.sum-note { margin: 6px 0 0; font-size: 12px; color: var(--wx-muted); }
/* 「引擎2」以徽标常驻在选大运卡上（FR-006：本页 MUST 标明这是引擎2 的数） */
.engine-badge {
  margin-left: 6px;
  font-size: 12px;
  font-weight: 400;
  color: #fff;
  background: var(--wx-primary-2, #a63431);
  border-radius: 8px;
  padding: 1px 7px;
}
</style>
