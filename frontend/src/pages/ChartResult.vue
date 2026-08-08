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

function goBack() {
  if (!result) router.replace('/')
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
  <div>
    <template v-if="result">
      <ChartDisplay :result="result" />
      <div class="actions">
        <van-button type="primary" block @click="onOpenSave">保存记录</van-button>
        <van-button plain type="primary" block :loading="generating" @click="onGenerateImage">
          生成长图
        </van-button>
      </div>
    </template>
    <van-empty v-else description="暂无排盘结果">
      <van-button type="primary" @click="goBack">去排盘</van-button>
    </van-empty>

    <van-popup v-model:show="showSavePopup" position="bottom" round>
      <div class="save-form">
        <h3>保存排盘记录</h3>
        <van-field v-model="personName" label="人物" placeholder="如：儿子" />
        <van-field name="relationship" label="关系">
          <template #input>
            <van-radio-group v-model="relationship" direction="horizontal">
              <van-radio name="SELF">本人</van-radio>
              <van-radio name="CHILD">子女</van-radio>
              <van-radio name="PARENT">父母</van-radio>
              <van-radio name="OTHER">其他</van-radio>
            </van-radio-group>
          </template>
        </van-field>
        <van-field v-model="notes" label="备注" placeholder="可选" />
        <div class="save-buttons">
          <van-button type="primary" block :loading="saving" @click="onSave">确认保存</van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<style scoped>
.actions {
  padding: 12px 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.save-form {
  padding: 16px;
}
.save-form h3 {
  text-align: center;
  margin: 0 0 12px;
}
.save-buttons {
  margin-top: 16px;
}
</style>
