<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { getRecord } from '../api/records'
import type { RecordDetail } from '../types'
import ChartDisplay from '../components/ChartDisplay.vue'

const route = useRoute()
const router = useRouter()
const record = ref<RecordDetail | null>(null)
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    record.value = await getRecord(Number(route.params.id))
  } catch (e) {
    showToast((e as Error).message)
    router.replace('/records')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <van-nav-bar title="记录详情" left-text="返回" @click-left="router.back()" />
    <van-loading v-if="loading" class="loading" />
    <template v-else-if="record">
      <ChartDisplay :result="record.chart_result" />
    </template>
  </div>
</template>

<style scoped>
.loading {
  margin: 40px auto;
}
</style>
