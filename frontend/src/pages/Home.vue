<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { predictChart } from '../api/charts'
import { searchGeo, type GeoCity } from '../api/geo'
import { useChartStore } from '../stores/chart'
import { useAuthStore } from '../stores/auth'
import type { BirthInput } from '../types'

const GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'] as const
const ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'] as const
const PILLAR_KEYS = ['year', 'month', 'day', 'time'] as const
type PillarKey = (typeof PILLAR_KEYS)[number]

const router = useRouter()
const chartStore = useChartStore()
const authStore = useAuthStore()

const calendar = ref<'solar' | 'lunar' | 'sizhu'>('solar')
const gender = ref<'M' | 'F' | 'UNKNOWN'>('M')
const name = ref('')
const birthDate = ref('1990-05-20')
const birthTime = ref('12:00')
const unknownTime = ref(false)
const birthPlace = ref('')
const birthLatitude = ref<number>()
const birthLongitude = ref<number>()
const birthTimezone = ref<string>()
const isLeapMonth = ref(false)
const loading = ref(false)

// 精确时辰（日出日落定位法）：默认关；登录用户偏好持久化（FR-001/FR-012）
const preciseShichen = ref(
  authStore.isLoggedIn && localStorage.getItem('precise_shichen') === 'true',
)
watch(preciseShichen, (v) => {
  if (authStore.isLoggedIn) localStorage.setItem('precise_shichen', String(v))
})

// 全球地点模糊搜索
const showGeoSearch = ref(false)
const geoQuery = ref('')
const geoResults = ref<GeoCity[]>([])
const geoSearching = ref(false)
let geoDebounce: number | undefined

// 四柱输入
const pillars = ref<Record<PillarKey, string>>({ year: '庚午', month: '辛巳', day: '乙酉', time: '辛巳' })
const pillarPickerKey = ref<PillarKey | null>(null)
const pillarModel = ref<[string, string]>(['甲', '子'])
const pillarColumns = [{ values: [...GAN] }, { values: [...ZHI] }]
const showPillarPicker = computed({
  get: () => pillarPickerKey.value !== null,
  set: (v: boolean) => {
    if (!v) pillarPickerKey.value = null
  },
})

// 日期/时间选择器
const showDatePicker = ref(false)
const showTimePicker = ref(false)
const dateModel = ref(['1990', '05', '20'])
const timeModel = ref(['12', '00'])
const minDate = new Date(1920, 0, 1)
const maxDate = new Date(new Date().getFullYear(), 11, 31)

const pillarLabels: Record<string, string> = { year: '年柱', month: '月柱', day: '日柱', time: '时柱' }
const isSizhu = computed(() => calendar.value === 'sizhu')
const isCalendarMode = computed(() => !isSizhu.value)

function openPillar(key: PillarKey) {
  pillarPickerKey.value = key
  const gz = pillars.value[key]
  pillarModel.value = [gz[0], gz[1]]
}

function onPillarConfirm() {
  if (pillarPickerKey.value) {
    pillars.value[pillarPickerKey.value] = pillarModel.value.join('')
  }
  pillarPickerKey.value = null
}

function onDateConfirm() {
  const [y, m, d] = dateModel.value
  birthDate.value = `${y}-${m}-${d}`
  showDatePicker.value = false
}

function onTimeConfirm() {
  const [h, m] = timeModel.value
  birthTime.value = `${h}:${m}`
  showTimePicker.value = false
}

function openGeoSearch() {
  showGeoSearch.value = true
  geoQuery.value = ''
  geoResults.value = []
}

function onGeoQuery() {
  if (geoDebounce) window.clearTimeout(geoDebounce)
  if (!geoQuery.value.trim()) {
    geoResults.value = []
    return
  }
  geoDebounce = window.setTimeout(async () => {
    geoSearching.value = true
    try {
      geoResults.value = (await searchGeo(geoQuery.value.trim())).items
    } catch {
      geoResults.value = []
    } finally {
      geoSearching.value = false
    }
  }, 300)
}

function geoLabel(city: GeoCity): string {
  if (city.name_zh) return city.admin1_zh ? `${city.name_zh} · ${city.admin1_zh}` : city.name_zh
  return city.name
}

function selectGeo(city: GeoCity) {
  birthPlace.value = geoLabel(city)
  birthLatitude.value = city.latitude
  birthLongitude.value = city.longitude
  birthTimezone.value = city.timezone ?? undefined
  showGeoSearch.value = false
}

async function onSubmit() {
  const base = { name: name.value || undefined, gender: gender.value }
  let input: BirthInput
  if (isSizhu.value) {
    input = { ...base, calendar: 'sizhu', birth_pillars: { ...pillars.value } }
  } else {
    input = {
      ...base,
      calendar: calendar.value,
      birth_date: birthDate.value,
      birth_time: unknownTime.value ? undefined : birthTime.value,
      birth_month_is_leap: isLeapMonth.value,
      birth_place: birthPlace.value || undefined,
      longitude: birthLongitude.value,
      latitude: birthLatitude.value,
      timezone: birthTimezone.value,
      precise_shichen: preciseShichen.value || undefined,
    }
  }
  loading.value = true
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
  <div class="home-page">
    <header class="hero">
      <h1>五行 · 八字排盘</h1>
      <p>输入出生信息 · 一窥命局喜忌</p>
    </header>

    <div class="wx-card">
      <p class="wx-card-title">出生信息</p>
      <van-cell-group :border="false">
        <van-field v-model="name" label="姓名" placeholder="可选" />
        <van-field name="calendar" label="历法">
          <template #input>
            <van-radio-group v-model="calendar" direction="horizontal">
              <van-radio name="solar" checked-color="#a63431">公历</van-radio>
              <van-radio name="lunar" checked-color="#a63431">农历</van-radio>
              <van-radio name="sizhu" checked-color="#a63431">四柱</van-radio>
            </van-radio-group>
          </template>
        </van-field>

        <!-- 四柱输入 -->
        <template v-if="isSizhu">
          <van-field
            v-for="key in PILLAR_KEYS"
            :key="key"
            :model-value="pillars[key]"
            :label="pillarLabels[key]"
            readonly
            is-link
            @click="openPillar(key)"
          />
        </template>

        <!-- 公历/农历输入 -->
        <template v-else>
          <van-field
            :model-value="birthDate"
            label="出生日期"
            readonly
            is-link
            @click="showDatePicker = true"
          />
          <van-field v-if="calendar === 'lunar'" name="leap" label="农历">
            <template #input>
              <van-checkbox v-model="isLeapMonth" checked-color="#a63431">闰月</van-checkbox>
            </template>
          </van-field>
          <van-field
            :model-value="unknownTime ? '时辰不详' : birthTime"
            label="出生时间"
            readonly
            :is-link="!unknownTime"
            @click="!unknownTime && (showTimePicker = true)"
          />
          <van-field name="time-unknown" label=" ">
            <template #input>
              <van-checkbox v-model="unknownTime" checked-color="#a63431">不知道时辰</van-checkbox>
            </template>
          </van-field>
          <van-field v-if="!unknownTime" name="precise-shichen" label=" ">
            <template #input>
              <van-checkbox v-model="preciseShichen" checked-color="#a63431">
                精确时辰（日出日落定位法）
              </van-checkbox>
            </template>
          </van-field>
          <van-field
            :model-value="birthPlace || '未选择'"
            label="出生地点"
            readonly
            is-link
            @click="openGeoSearch"
          />
        </template>

        <van-field name="gender" label="性别">
          <template #input>
            <van-radio-group v-model="gender" direction="horizontal">
              <van-radio name="M" checked-color="#a63431">男</van-radio>
              <van-radio name="F" checked-color="#a63431">女</van-radio>
              <van-radio name="UNKNOWN" checked-color="#a63431">不详</van-radio>
            </van-radio-group>
          </template>
        </van-field>
      </van-cell-group>

      <div class="submit">
        <van-button
          type="primary"
          block
          class="wx-btn-primary"
          :loading="loading"
          @click="onSubmit"
        >
          开始排盘
        </van-button>
      </div>
    </div>

    <!-- 日期选择器（年月日一次滑动） -->
    <van-popup v-model:show="showDatePicker" position="bottom" round>
      <van-date-picker
        v-model="dateModel"
        title="选择出生日期"
        :min-date="minDate"
        :max-date="maxDate"
        :columns-type="['year', 'month', 'day']"
        @confirm="onDateConfirm"
        @cancel="showDatePicker = false"
      />
    </van-popup>

    <!-- 时间选择器 -->
    <van-popup v-model:show="showTimePicker" position="bottom" round>
      <van-time-picker
        v-model="timeModel"
        title="选择出生时间"
        @confirm="onTimeConfirm"
        @cancel="showTimePicker = false"
      />
    </van-popup>

    <!-- 全球地点模糊搜索 -->
    <van-popup v-model:show="showGeoSearch" position="bottom" round>
      <div class="geo-search">
        <van-search
          v-model="geoQuery"
          placeholder="搜索全球城市，如：北京 / London"
          @update:model-value="onGeoQuery"
        />
        <van-loading v-if="geoSearching" class="geo-loading" />
        <van-cell
          v-for="c in geoResults"
          :key="c.name + c.latitude"
          :title="geoLabel(c)"
          :label="c.country_code ?? ''"
          is-link
          @click="selectGeo(c)"
        />
        <van-empty
          v-if="!geoSearching && geoQuery && geoResults.length === 0"
          description="未找到该城市"
        />
      </div>
    </van-popup>

    <!-- 四柱干支选择器（天干 + 地支两列） -->
    <van-popup v-model:show="showPillarPicker" position="bottom" round>
      <van-picker
        v-model="pillarModel"
        title="选择干支"
        :columns="pillarColumns"
        @confirm="onPillarConfirm"
        @cancel="pillarPickerKey = null"
      />
    </van-popup>
  </div>
</template>

<style scoped>
.home-page {
  padding-bottom: 20px;
}
.submit {
  margin: 18px 0 2px;
}
.geo-loading {
  margin: 16px auto;
}
</style>
