<script setup lang="ts">
/** 015：格局喜忌摘要卡（结果页原局 / 当前大运各一张）。 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { GeJuRef, GeJuStrength } from '../types'
import { GEJU_STATUS_LABEL, gejuName, strengthText } from '../utils/geju'

const props = defineProps<{
  title: string
  ge: GeJuRef | null
  status: string
  strength?: GeJuStrength | null
  gaoDi?: string | null
  change?: { type: string | null; reason: string } | null
  to: string
  testid?: string
}>()

const router = useRouter()
const statusLabel = computed(() => GEJU_STATUS_LABEL[props.status] ?? props.status)
</script>

<template>
  <section class="wx-card" :data-testid="props.testid || 'geju-summary'">
    <p class="wx-card-title">
      {{ props.title }}
      <span class="strength-link" data-testid="geju-detail-link" @click="router.push(props.to)">
        查看详情<van-icon name="arrow" size="12" />
      </span>
    </p>
    <template v-if="props.ge">
      <p class="ge-name" data-testid="geju-name">{{ gejuName(props.ge) }}</p>
      <p class="ge-meta">
        <span class="badge" :data-status="props.status" data-testid="geju-status">{{ statusLabel }}</span>
        <span data-testid="geju-strength">{{ strengthText(props.strength) }}</span>
        <span v-if="props.gaoDi" data-testid="geju-gaodi">层次 {{ props.gaoDi }}</span>
        <span v-if="props.change?.type" class="change" data-testid="geju-change">{{ props.change.type }}</span>
      </p>
      <p v-if="props.status === 'undetermined'" class="muted" data-testid="geju-undetermined">
        存疑/未定：完整条件与书证见详情。
      </p>
    </template>
    <p v-else class="muted" data-testid="geju-empty">未定（没有可用格名）</p>
  </section>
</template>

<style scoped>
.ge-name {
  margin: 2px 0 6px;
  font-size: 18px;
  font-weight: 600;
}
.ge-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin: 0;
  font-size: 13px;
  color: var(--wx-text, #333);
}
.badge {
  border-radius: 10px;
  padding: 1px 8px;
  font-size: 12px;
  color: #fff;
  background: var(--wx-primary-2, #a63431);
}
.badge[data-status='undetermined'] {
  background: #8a8a8a;
}
.badge[data-status='po'] {
  background: #6b6b6b;
}
.change {
  color: var(--wx-primary-2, #a63431);
  font-weight: 600;
}
.muted {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--wx-muted, #888);
}
.strength-link {
  margin-left: 6px;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  background: var(--wx-primary-2, #a63431);
  border-radius: 10px;
  padding: 1px 8px;
  cursor: pointer;
  vertical-align: middle;
}
</style>
