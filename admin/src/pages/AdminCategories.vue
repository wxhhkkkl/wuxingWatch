<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createCategory,
  deleteCategory,
  listCategories,
  updateCategory,
  type AdminCategory,
} from '../api/adminBooks'

const items = ref<AdminCategory[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref<AdminCategory | null>(null)
const form = ref({ name: '', sort_order: 0 })

async function load() {
  loading.value = true
  try {
    items.value = (await listCategories()).items
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    loading.value = false
  }
}

function openAdd() {
  editing.value = null
  form.value = { name: '', sort_order: items.value.length }
  dialogVisible.value = true
}

function openEdit(c: AdminCategory) {
  editing.value = c
  form.value = { name: c.name, sort_order: c.sort_order }
  dialogVisible.value = true
}

async function onSave() {
  try {
    if (editing.value) await updateCategory(editing.value.id, form.value)
    else await createCategory(form.value)
    ElMessage.success('已保存')
    dialogVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}

async function onDelete(c: AdminCategory) {
  try {
    await ElMessageBox.confirm(
      `确定删除「${c.name}」？其下书籍将变为未分类。`,
      '删除分类',
      { type: 'warning' },
    )
    await deleteCategory(c.id)
    ElMessage.success('已删除')
    await load()
  } catch {
    /* 取消 */
  }
}

onMounted(load)
</script>

<template>
  <el-card>
    <template #header>
      <div class="header">
        <span class="title">分类管理</span>
        <el-button type="primary" @click="openAdd">新增分类</el-button>
      </div>
    </template>
    <el-table v-loading="loading" :data="items" empty-text="暂无数据">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="分类名" />
      <el-table-column prop="sort_order" label="序号" width="90" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="dialogVisible" :title="editing ? '编辑分类' : '新增分类'" width="420px">
    <el-form label-width="70px">
      <el-form-item label="分类名">
        <el-input v-model="form.name" maxlength="50" placeholder="如：命理" />
      </el-form-item>
      <el-form-item label="序号">
        <el-input-number v-model="form.sort_order" :min="0" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="onSave">保存</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.title {
  font-weight: 600;
}
</style>
