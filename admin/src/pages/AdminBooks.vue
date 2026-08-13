<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  deleteBook,
  listBooks,
  listCategories,
  type AdminBook,
  type AdminCategory,
} from '../api/adminBooks'

const router = useRouter()
const items = ref<AdminBook[]>([])
const categories = ref<AdminCategory[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const categoryId = ref<number | undefined>(undefined)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await listBooks({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      category_id: categoryId.value,
    })
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

async function onDelete(b: AdminBook) {
  try {
    await ElMessageBox.confirm(`确定删除「${b.title}」？其章节将一并删除。`, '删除书籍', {
      type: 'warning',
    })
    await deleteBook(b.id)
    ElMessage.success('已删除')
    load()
  } catch {
    /* 取消 */
  }
}

const catName = (id: number | null) => categories.value.find((c) => c.id === id)?.name ?? '未分类'

onMounted(() => {
  listCategories()
    .then((r) => (categories.value = r.items))
    .catch(() => {})
  load()
})
</script>

<template>
  <el-card>
    <template #header>
      <div class="header">
        <span class="title">书籍管理</span>
        <div class="tools">
          <el-input
            v-model="keyword"
            placeholder="按书名搜索"
            clearable
            style="width: 200px"
            @keyup.enter="onSearch"
            @clear="onSearch"
          />
          <el-select
            v-model="categoryId"
            placeholder="全部分类"
            clearable
            style="width: 140px"
            @change="onSearch"
          >
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
          <el-button type="primary" @click="router.push('/books/new')">新增书籍</el-button>
        </div>
      </div>
    </template>

    <el-table v-loading="loading" :data="items" empty-text="暂无数据">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="书名" min-width="180" />
      <el-table-column label="分类" width="110">
        <template #default="{ row }">{{ catName(row.category_id) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'published' ? 'success' : 'warning'">
            {{ row.status === 'published' ? '已发布' : '草稿' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="chapter_count" label="章节数" width="90" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button size="small" @click="router.push(`/books/${row.id}`)">编辑</el-button>
          <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      class="pager"
      layout="total, prev, pager, next"
      :total="total"
      :page-size="pageSize"
      :current-page="page"
      @current-change="onPageChange"
    />
  </el-card>
</template>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.tools {
  display: flex;
  gap: 8px;
}
.title {
  font-weight: 600;
}
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
