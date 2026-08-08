<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listMembers, type MemberListItem } from '../api/members'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const items = ref<MemberListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const phone = ref('')
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await listMembers({ page: page.value, page_size: pageSize.value, phone: phone.value || undefined })
    items.value = data.items
    total.value = data.total
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  load()
}

function onPageChange(p: number) {
  page.value = p
  load()
}

function onLogout() {
  auth.logout()
  router.replace('/login')
}

onMounted(load)
</script>

<template>
  <div class="members-page">
    <el-card>
      <template #header>
        <div class="header">
          <span class="title">会员管理</span>
          <div class="tools">
            <el-input
              v-model="phone"
              placeholder="按手机号搜索"
              clearable
              style="width: 220px"
              @keyup.enter="onSearch"
              @clear="onSearch"
            />
            <el-button type="primary" @click="onSearch">搜索</el-button>
            <el-button @click="onLogout">退出</el-button>
          </div>
        </div>
      </template>

      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="phone_masked" label="手机号" />
        <el-table-column prop="chart_count" label="排盘数" width="90" />
        <el-table-column prop="created_at" label="注册时间">
          <template #default="{ row }">{{ row.created_at.slice(0, 16) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="router.push(`/members/${row.id}`)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <span class="total">会员总数：{{ total }}</span>
        <el-pagination
          background
          layout="prev, pager, next"
          :total="total"
          :page-size="pageSize"
          :current-page="page"
          @current-change="onPageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.members-page {
  padding: 20px;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.title {
  font-weight: 600;
  font-size: 16px;
}
.tools {
  display: flex;
  gap: 8px;
}
.pager {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
}
.total {
  color: #888;
  font-size: 13px;
}
</style>
