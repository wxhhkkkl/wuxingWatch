<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createBook,
  createChapter,
  deleteChapter,
  getBook,
  listCategories,
  listChapters,
  publishBook,
  reorderChapters,
  unpublishBook,
  updateBook,
  updateChapter,
  type AdminBook,
  type AdminCategory,
  type AdminChapter,
} from '../api/adminBooks'
import { renderMarkdown } from '../utils/markdown'

const route = useRoute()
const router = useRouter()
const isNew = computed(() => route.params.id === 'new')
const bookId = computed(() => Number(route.params.id))

const form = ref({
  title: '',
  author: '',
  description: '',
  cover_url: '',
  category_id: undefined as number | undefined,
})
const categories = ref<AdminCategory[]>([])
const book = ref<AdminBook | null>(null)
const saving = ref(false)

const chapters = ref<AdminChapter[]>([])
const chapterDialog = ref(false)
const editingChapter = ref<AdminChapter | null>(null)
const chapterForm = ref({ title: '', content: '' })
const chapterPreview = ref(false)

async function load() {
  if (isNew.value) return
  try {
    book.value = await getBook(bookId.value)
    form.value = {
      title: book.value.title,
      author: book.value.author ?? '',
      description: book.value.description ?? '',
      cover_url: book.value.cover_url ?? '',
      category_id: book.value.category_id ?? undefined,
    }
  } catch (e) {
    ElMessage.error((e as Error).message)
    router.back()
  }
}

async function loadChapters() {
  if (isNew.value) return
  try {
    chapters.value = (await listChapters(bookId.value)).items
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}

async function onSave() {
  if (!form.value.title.trim()) {
    ElMessage.warning('请输入书名')
    return
  }
  if (!form.value.category_id) {
    ElMessage.warning('请选择分类')
    return
  }
  saving.value = true
  try {
    const data = {
      title: form.value.title,
      author: form.value.author || null,
      description: form.value.description || null,
      cover_url: form.value.cover_url || null,
      category_id: form.value.category_id,
    }
    if (isNew.value) {
      await createBook(data)
      ElMessage.success('已创建')
    } else {
      await updateBook(bookId.value, data)
      ElMessage.success('已保存')
    }
    router.replace('/books')
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    saving.value = false
  }
}

async function onPublish() {
  try {
    await publishBook(bookId.value)
    ElMessage.success('已发布')
    book.value = await getBook(bookId.value)
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}

async function onUnpublish() {
  try {
    await unpublishBook(bookId.value)
    ElMessage.success('已取消发布')
    book.value = await getBook(bookId.value)
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}

function openChapterAdd() {
  editingChapter.value = null
  chapterForm.value = { title: '', content: '' }
  chapterPreview.value = false
  chapterDialog.value = true
}

function openChapterEdit(c: AdminChapter) {
  editingChapter.value = c
  chapterForm.value = { title: c.title, content: c.content ?? '' }
  chapterPreview.value = false
  chapterDialog.value = true
}

async function onChapterSave() {
  if (!chapterForm.value.title.trim()) {
    ElMessage.warning('请输入章节标题')
    return
  }
  try {
    if (editingChapter.value) {
      await updateChapter(bookId.value, editingChapter.value.id, chapterForm.value)
    } else {
      await createChapter(bookId.value, chapterForm.value)
    }
    ElMessage.success('已保存')
    chapterDialog.value = false
    await loadChapters()
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}

async function onChapterDelete(c: AdminChapter) {
  try {
    await ElMessageBox.confirm(`确定删除「${c.title}」？`, '删除章节', { type: 'warning' })
    await deleteChapter(bookId.value, c.id)
    ElMessage.success('已删除')
    await loadChapters()
  } catch {
    /* 取消 */
  }
}

async function onMove(c: AdminChapter, dir: -1 | 1) {
  const idx = chapters.value.findIndex((x) => x.id === c.id)
  const j = idx + dir
  if (j < 0 || j >= chapters.value.length) return
  const arr = chapters.value.map((x) => x.id)
  ;[arr[idx], arr[j]] = [arr[j], arr[idx]]
  try {
    await reorderChapters(bookId.value, arr)
    await loadChapters()
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}

onMounted(() => {
  listCategories()
    .then((r) => (categories.value = r.items))
    .catch(() => {})
  load()
  loadChapters()
})
</script>

<template>
  <el-card>
    <template #header>
      <div class="header">
        <span class="title">{{ isNew ? '新增书籍' : `编辑书籍：${book?.title ?? ''}` }}</span>
        <div v-if="book" class="status">
          <el-tag :type="book.status === 'published' ? 'success' : 'warning'">
            {{ book.status === 'published' ? '已发布' : '草稿' }}
          </el-tag>
          <el-button v-if="book.status === 'draft'" size="small" type="success" @click="onPublish">
            发布
          </el-button>
          <el-button v-else size="small" type="warning" @click="onUnpublish">取消发布</el-button>
        </div>
      </div>
    </template>

    <el-form label-width="80px" style="max-width: 520px">
      <el-form-item label="书名" required>
        <el-input v-model="form.title" maxlength="100" placeholder="必填" />
      </el-form-item>
      <el-form-item label="分类" required>
        <el-select v-model="form.category_id" placeholder="选择分类" style="width: 200px">
          <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="作者">
        <el-input v-model="form.author" maxlength="50" />
      </el-form-item>
      <el-form-item label="简介">
        <el-input v-model="form.description" type="textarea" :rows="3" maxlength="500" />
      </el-form-item>
      <el-form-item label="封面 URL">
        <el-input v-model="form.cover_url" maxlength="500" placeholder="https://…" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="onSave">
          {{ isNew ? '创建书籍' : '保存' }}
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>

  <el-card v-if="!isNew" style="margin-top: 16px">
    <template #header>
      <div class="header">
        <span class="title">章节（{{ chapters.length }}）</span>
        <el-button type="primary" size="small" @click="openChapterAdd">新增章节</el-button>
      </div>
    </template>
    <el-table :data="chapters" empty-text="暂无章节">
      <el-table-column prop="sort_order" label="#" width="60" />
      <el-table-column prop="title" label="章节标题" min-width="200" />
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button size="small" text @click="onMove(row, -1)">上移</el-button>
          <el-button size="small" text @click="onMove(row, 1)">下移</el-button>
          <el-button size="small" @click="openChapterEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="onChapterDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-dialog
    v-model="chapterDialog"
    :title="editingChapter ? '编辑章节' : '新增章节'"
    width="640px"
  >
    <el-form label-width="60px">
      <el-form-item label="标题" required>
        <el-input v-model="chapterForm.title" maxlength="100" placeholder="必填" />
      </el-form-item>
      <el-form-item label="内容">
        <div class="md-editor">
          <el-radio-group v-model="chapterPreview" size="small">
            <el-radio-button :value="false">编辑</el-radio-button>
            <el-radio-button :value="true">预览</el-radio-button>
          </el-radio-group>
          <el-input
            v-if="!chapterPreview"
            v-model="chapterForm.content"
            type="textarea"
            :rows="12"
            placeholder="支持 Markdown：标题、列表、加粗…"
          />
          <div v-else class="md-preview" v-html="renderMarkdown(chapterForm.content)" />
        </div>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="chapterDialog = false">取消</el-button>
      <el-button type="primary" @click="onChapterSave">保存</el-button>
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
.status {
  display: flex;
  align-items: center;
  gap: 8px;
}
.md-editor {
  width: 100%;
}
.md-preview {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
  min-height: 200px;
  line-height: 1.7;
}
</style>
