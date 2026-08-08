<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { predictChart } from '../api/charts'
import { useChartStore } from '../stores/chart'
import type { BirthInput } from '../types'

const router = useRouter()
const chartStore = useChartStore()

const calendar = ref<'solar' | 'lunar'>('solar')
const gender = ref<'M' | 'F' | 'UNKNOWN'>('UNKNOWN')
const name = ref('')
const birthDate = ref('1990-05-20')
const birthTime = ref('')
const birthPlace = ref('北京市')
const isLeapMonth = ref(false)
const loading = ref(false)

async function onSubmit() {
  if (!birthDate.value) {
    showToast('请选择出生日期')
    return
  }
  loading.value = true
  const input: BirthInput = {
    name: name.value || undefined,
    gender: gender.value,
    calendar: calendar.value,
    birth_date: birthDate.value,
    birth_time: birthTime.value || undefined,
    birth_month_is_leap: isLeapMonth.value,
    birth_place: birthPlace.value || undefined,
  }
  try {
    const result = await predictChart(input)
    chartStore.set(result, input)
    router.push('/result')
  } catch (e) {
    showToast((e as Error).message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <h1 class="title">五行 · 八字排盘</h1>
    <van-cell-group inset>
      <van-field v-model="name" label="姓名" placeholder="可选" />
      <van-field name="calendar" label="历法">
        <template #input>
          <van-radio-group v-model="calendar" direction="horizontal">
            <van-radio name="solar">公历</van-radio>
            <van-radio name="lunar">农历</van-radio>
          </van-radio-group>
        </template>
      </van-field>
      <van-field v-model="birthDate" label="出生日期" type="date" placeholder="选择日期" />
      <van-field v-if="calendar === 'lunar'" name="leap" label="农历">
        <template #input>
          <van-checkbox v-model="isLeapMonth">闰月</van-checkbox>
        </template>
      </van-field>
      <van-field v-model="birthTime" label="出生时间" type="time" placeholder="可留空（时辰不详）" />
      <van-field v-model="birthPlace" label="出生地点" placeholder="如：北京市" />
      <van-field name="gender" label="性别">
        <template #input>
          <van-radio-group v-model="gender" direction="horizontal">
            <van-radio name="M">男</van-radio>
            <van-radio name="F">女</van-radio>
            <van-radio name="UNKNOWN">不详</van-radio>
          </van-radio-group>
        </template>
      </van-field>
    </van-cell-group>
    <div class="submit">
      <van-button type="primary" block :loading="loading" @click="onSubmit">开始排盘</van-button>
    </div>
  </div>
</template>

<style scoped>
.page {
  padding: 16px 0 32px;
}
.title {
  text-align: center;
  font-size: 22px;
  color: #8c2f39;
  margin: 8px 0 20px;
}
.submit {
  margin: 24px 16px;
}
</style>
