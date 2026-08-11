<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showSuccessToast, showToast } from 'vant'
import { useChartStore } from '../stores/chart'
import { useAuthStore } from '../stores/auth'
import { fetchChartImage } from '../api/charts'
import { saveRecord, type SaveRecordInput } from '../api/records'
import ChartDisplay from '../components/ChartDisplay.vue'

const chartStore = useChartStore()
const authStore = useAuthStore()
const router = useRouter()

const result = chartStore.result
const inputs = chartStore.inputs

const showSavePopup = ref(false)
const personName = ref('')
const relationship = ref<'SELF' | 'CHILD' | 'PARENT' | 'OTHER'>('SELF')
const notes = ref('')
const saving = ref(false)
const generating = ref(false)
const showMenu = ref(false)
const menuActions = [{ name: '修改内容' }]

function goBack() {
  if (!result) router.replace('/')
}

function onEdit() {
  showMenu.value = false
  if (!inputs) return
  chartStore.setEditDraft({ recordId: null, input: { ...inputs } })
  router.push('/')
}

async function onOpenSave() {
  if (!authStore.isLoggedIn) {
    showToast('请先登录后再保存')
    router.push('/login')
    return
  }
  showSavePopup.value = true
}

async function onSave() {
  saving.value = true
  try {
    await saveRecord({
      ...(inputs as SaveRecordInput),
      person_name: personName.value || undefined,
      relationship: relationship.value,
      notes: notes.value || undefined,
    })
    showSuccessToast('已保存')
    showSavePopup.value = false
  } catch (e) {
    showToast((e as Error).message)
  } finally {
    saving.value = false
  }
}

async function onGenerateImage() {
  if (!inputs) return
  generating.value = true
  try {
    const blob = await fetchChartImage(inputs)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = '命盘.png'
    a.click()
    URL.revokeObjectURL(url)
    showSuccessToast('已生成图片，可保存/分享')
  } catch (e) {
    showToast((e as Error).message)
  } finally {
    generating.value = false
  }
}
</script>

<template>
  <div class="result-page">
    <van-nav-bar title="排盘结果" left-text="返回" left-arrow @click-left="router.back()">
      <template #right>
        <van-icon v-if="result" name="ellipsis" size="20" @click="showMenu = true" />
      </template>
    </van-nav-bar>

    <van-action-sheet v-model:show="showMenu" :actions="menuActions" @select="onEdit" />

    <template v-if="result">
      <ChartDisplay :result="result" />

      <!-- 底部操作栏 -->
      <div class="action-bar">
        <van-button class="action-btn" plain type="primary" :loading="generating" @click="onGenerateImage">
          生成长图
        </van-button>
        <van-button class="action-btn" type="primary" @click="onOpenSave">保存记录</van-button>
      </div>
    </template>

    <van-empty v-else description="暂无排盘结果">
      <van-button type="primary" @click="goBack">去排盘</van-button>
    </van-empty>

    <!-- 保存弹窗 -->
    <van-popup v-model:show="showSavePopup" position="bottom" round>
      <div class="save-form">
        <p class="save-title">保存排盘记录</p>
        <van-field v-model="personName" label="人物" placeholder="如：儿子" />
        <van-field name="relationship" label="关系">
          <template #input>
            <van-radio-group v-model="relationship" direction="horizontal">
              <van-radio name="SELF" checked-color="#a63431">本人</van-radio>
              <van-radio name="CHILD" checked-color="#a63431">子女</van-radio>
              <van-radio name="PARENT" checked-color="#a63431">父母</van-radio>
              <van-radio name="OTHER" checked-color="#a63431">其他</van-radio>
            </van-radio-group>
          </template>
        </van-field>
        <van-field v-model="notes" label="备注" placeholder="可选" />
        <div class="save-buttons">
          <van-button type="primary" class="wx-btn-primary" block :loading="saving" @click="onSave">
            确认保存
          </van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<style scoped>
.result-page {
  padding-bottom: 84px;
}
.action-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  max-width: 480px;
  margin: 0 auto;
  display: flex;
  gap: 10px;
  padding: 10px 14px calc(10px + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.96);
  border-top: 1px solid var(--wx-line);
  backdrop-filter: blur(8px);
}
.action-btn {
  flex: 1;
  border-radius: 24px;
  height: 44px;
}
.save-form {
  padding: 18px 16px calc(18px + env(safe-area-inset-bottom));
}
.save-title {
  text-align: center;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 12px;
}
.save-buttons {
  margin-top: 16px;
}
</style>
