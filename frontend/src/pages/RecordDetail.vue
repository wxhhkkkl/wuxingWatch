<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { getRecord } from '../api/records'
import { useChartStore } from '../stores/chart'
import type { RecordDetail } from '../types'
import ChartDisplay from '../components/ChartDisplay.vue'

const route = useRoute()
const router = useRouter()
const chartStore = useChartStore()
const record = ref<RecordDetail | null>(null)
const loading = ref(false)
const showMenu = ref(false)
const menuActions = [{ name: '修改内容' }]

function onEdit() {
  showMenu.value = false
  if (!record.value?.birth_input) {
    showToast('该记录缺少出生信息，无法修改')
    return
  }
  chartStore.setEditDraft({
    recordId: record.value.id,
    input: record.value.birth_input,
    meta: {
      person_name: record.value.person_name,
      relationship: record.value.relationship as 'SELF' | 'CHILD' | 'PARENT' | 'OTHER',
      notes: record.value.notes,
    },
  })
  router.push('/')
}

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
    <van-nav-bar title="记录详情" left-text="返回" @click-left="router.back()">
      <template #right>
        <van-icon v-if="record" name="ellipsis" size="20" @click="showMenu = true" />
      </template>
    </van-nav-bar>
    <van-action-sheet v-model:show="showMenu" :actions="menuActions" @select="onEdit" />
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
