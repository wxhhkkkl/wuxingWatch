<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getChart, getMember, listMemberCharts, type ChartSummary, type MemberDetail } from '../api/members'

const route = useRoute()
const router = useRouter()
const id = Number(route.params.id)
const member = ref<MemberDetail | null>(null)
const charts = ref<ChartSummary[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    member.value = await getMember(id)
    charts.value = (await listMemberCharts(id)).items
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    loading.value = false
  }
}

async function openChart(chartId: number) {
  try {
    const data = await getChart(chartId)
    const text = JSON.stringify(data.chart_result, null, 2)
    ElMessageBox.alert(text, '排盘详情', {
      customStyle: { maxHeight: '70vh', overflow: 'auto' },
      message: `<pre style="max-height:60vh;overflow:auto;white-space:pre-wrap">${text}</pre>`,
      dangerouslyUseHTMLString: true,
    })
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}

onMounted(load)
</script>

<template>
  <div class="detail-page">
    <el-page-header content="会员详情" @back="router.back()" />

    <el-card v-if="member" v-loading="loading" style="margin-top: 16px">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="ID">{{ member.id }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ member.phone }}</el-descriptions-item>
        <el-descriptions-item label="排盘数">{{ member.chart_count }}</el-descriptions-item>
        <el-descriptions-item label="注册时间">{{ member.created_at.slice(0, 16) }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>排盘记录</template>
      <el-table :data="charts" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="person_name" label="人物">
          <template #default="{ row }">{{ row.person_name ?? '未命名' }}</template>
        </el-table-column>
        <el-table-column prop="relationship" label="关系" width="90" />
        <el-table-column prop="created_at" label="保存时间">
          <template #default="{ row }">{{ row.created_at.slice(0, 16) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openChart(row.id)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.detail-page {
  padding: 20px;
}
</style>
