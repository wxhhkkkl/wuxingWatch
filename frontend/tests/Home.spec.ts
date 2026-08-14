import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const push = vi.fn()
const replace = vi.fn()
const currentRoute = { value: { fullPath: '/' } }

vi.mock('vue-router', () => ({
  useRouter: () => ({ push, replace, currentRoute }),
}))

vi.mock('../src/api/charts', () => ({
  predictChart: vi.fn(),
}))

vi.mock('../src/api/records', () => ({
  saveRecord: vi.fn(),
  updateRecord: vi.fn(),
}))

import Home from '../src/pages/Home.vue'
import { predictChart } from '../src/api/charts'
import { saveRecord, updateRecord } from '../src/api/records'
import { useChartStore } from '../src/stores/chart'
import { useAuthStore } from '../src/stores/auth'

const flush = () => new Promise((r) => setTimeout(r))
const loggedInUser = { id: 1, phone: '13800000000' }

describe('Home', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.removeItem('precise_shichen')
    push.mockClear()
    replace.mockClear()
    vi.mocked(predictChart).mockReset()
    vi.mocked(saveRecord).mockReset()
    vi.mocked(updateRecord).mockReset()
  })

  it('renders the title and input form', () => {
    const wrapper = mount(Home)
    expect(wrapper.text()).toContain('五行 · 八字排盘')
    expect(wrapper.find('button').exists()).toBe(true)
  })

  it('shows leap-month option when switching to lunar', async () => {
    const wrapper = mount(Home)
    expect(wrapper.text()).not.toContain('闰月')
    ;(wrapper.vm as unknown as { calendar: string }).calendar = 'lunar'
    await flush()
    expect(wrapper.text()).toContain('闰月')
  })

  // ---------- 登录校验 ----------

  it('redirects to login instead of charting when not logged in', async () => {
    const wrapper = mount(Home)
    await wrapper.find('button').trigger('click')
    await flush()
    expect(saveRecord).not.toHaveBeenCalled()
    expect(predictChart).not.toHaveBeenCalled()
    expect(push).toHaveBeenCalledWith({ name: 'login', query: { redirect: '/' } })
  })

  it('submits the form and navigates to the result page', async () => {
    useAuthStore().user = loggedInUser
    vi.mocked(saveRecord).mockResolvedValue({
      id: 1,
      chart_result: { day_master: '乙' },
    } as never)
    const wrapper = mount(Home)
    await wrapper.find('button').trigger('click')
    await flush()
    expect(saveRecord).toHaveBeenCalledTimes(1)
    expect(predictChart).not.toHaveBeenCalled()
    expect(push).toHaveBeenCalledWith('/result')
  })

  it('shows an error toast when the chart cannot be produced', async () => {
    useAuthStore().user = loggedInUser
    vi.mocked(saveRecord).mockRejectedValue(new Error('保存失败'))
    vi.mocked(predictChart).mockRejectedValue(new Error('排盘失败'))
    const wrapper = mount(Home)
    await wrapper.find('button').trigger('click')
    await flush()
    expect(push).not.toHaveBeenCalled()
  })

  // ---------- T103: 精确时辰开关 ----------

  it('shows the precise-shichen toggle in solar mode with known time', () => {
    const wrapper = mount(Home)
    expect(wrapper.text()).toContain('精确时辰')
  })

  it('hides the toggle in sizhu mode or when birth time is unknown', async () => {
    const wrapper = mount(Home)
    ;(wrapper.vm as unknown as { calendar: string }).calendar = 'sizhu'
    await flush()
    expect(wrapper.text()).not.toContain('精确时辰')
    ;(wrapper.vm as unknown as { calendar: string }).calendar = 'solar'
    ;(wrapper.vm as unknown as { unknownTime: boolean }).unknownTime = true
    await flush()
    expect(wrapper.text()).not.toContain('精确时辰')
  })

  it('submits precise_shichen: true when the toggle is on', async () => {
    useAuthStore().user = loggedInUser
    vi.mocked(saveRecord).mockResolvedValue({
      id: 1,
      chart_result: { day_master: '乙' },
    } as never)
    const wrapper = mount(Home)
    ;(wrapper.vm as unknown as { preciseShichen: boolean }).preciseShichen = true
    await flush()
    await wrapper.find('button').trigger('click')
    await flush()
    const payload = vi.mocked(saveRecord).mock.calls[0][0] as { precise_shichen?: boolean }
    expect(payload.precise_shichen).toBe(true)
  })

  it('omits precise_shichen when the toggle is off', async () => {
    useAuthStore().user = loggedInUser
    vi.mocked(saveRecord).mockResolvedValue({
      id: 1,
      chart_result: { day_master: '乙' },
    } as never)
    const wrapper = mount(Home)
    await wrapper.find('button').trigger('click')
    await flush()
    const payload = vi.mocked(saveRecord).mock.calls[0][0] as { precise_shichen?: boolean }
    expect(payload.precise_shichen).toBeFalsy()
  })

  it('persists the toggle for logged-in users and restores on reload', async () => {
    useAuthStore().user = loggedInUser
    const wrapper = mount(Home)
    ;(wrapper.vm as unknown as { preciseShichen: boolean }).preciseShichen = true
    await flush()
    expect(localStorage.getItem('precise_shichen')).toBe('true')
    wrapper.unmount()
    const wrapper2 = mount(Home)
    expect((wrapper2.vm as unknown as { preciseShichen: boolean }).preciseShichen).toBe(true)
  })

  it('does not persist the toggle for guests', async () => {
    const wrapper = mount(Home)
    ;(wrapper.vm as unknown as { preciseShichen: boolean }).preciseShichen = true
    await flush()
    expect(localStorage.getItem('precise_shichen')).toBeNull()
  })

  // ---------- 出生地点默认北京 ----------

  it('defaults birth place to Beijing with coordinates and timezone', () => {
    const wrapper = mount(Home)
    const vm = wrapper.vm as unknown as {
      birthPlace: string
      birthLatitude: number | undefined
      birthLongitude: number | undefined
      birthTimezone: string | undefined
    }
    expect(vm.birthPlace).toBe('北京')
    expect(vm.birthLongitude).toBe(116.41)
    expect(vm.birthLatitude).toBe(39.9)
    expect(vm.birthTimezone).toBe('Asia/Shanghai')
  })

  // ---------- 四柱输入 ----------

  it('formats pillar picker columns as { text, value } pairs (Vant 4)', async () => {
    const wrapper = mount(Home)
    const vm = wrapper.vm as unknown as {
      pillarColumns: Array<Array<{ text: string; value: string }>>
    }
    expect(vm.pillarColumns).toHaveLength(2)
    expect(vm.pillarColumns[0]).toHaveLength(10)
    expect(vm.pillarColumns[1]).toHaveLength(12)
    for (const col of vm.pillarColumns) {
      for (const opt of col) {
        expect(opt).toHaveProperty('text')
        expect(opt).toHaveProperty('value')
      }
    }
    expect(vm.pillarColumns[0][0]).toEqual({ text: '甲', value: '甲' })
    expect(vm.pillarColumns[1][0]).toEqual({ text: '子', value: '子' })
  })

  it('seeds the pillar model when opening a pillar field', async () => {
    const wrapper = mount(Home)
    const vm = wrapper.vm as unknown as {
      calendar: string
      openPillar: (k: string) => void
      pillarModel: [string, string]
      pillarPickerKey: string | null
    }
    vm.calendar = 'sizhu'
    await flush()
    vm.openPillar('day')
    expect(vm.pillarPickerKey).toBe('day')
    expect(vm.pillarModel).toEqual(['乙', '酉'])
  })

  // ---------- 性别选项 ----------

  it('does not offer an unknown gender option', () => {
    const wrapper = mount(Home)
    expect(wrapper.text()).not.toContain('不详')
    expect(wrapper.text()).toContain('男')
    expect(wrapper.text()).toContain('女')
  })

  // ---------- 修改内容（editDraft） ----------

  it('prefills the form from an edit draft', async () => {
    useChartStore().setEditDraft({
      recordId: 7,
      input: {
        gender: 'F',
        calendar: 'solar',
        name: '小明',
        birth_date: '2022-04-28',
        birth_time: '23:49',
        birth_place: '北京市',
        longitude: 116.41,
        latitude: 39.9,
      },
      meta: { person_name: '儿子', relationship: 'CHILD' },
    })
    const wrapper = mount(Home)
    await flush()
    const vm = wrapper.vm as unknown as {
      name: string
      gender: string
      birthDate: string
      birthTime: string
      birthPlace: string
    }
    expect(vm.name).toBe('小明')
    expect(vm.gender).toBe('F')
    expect(vm.birthDate).toBe('2022-04-28')
    expect(vm.birthTime).toBe('23:49')
    expect(vm.birthPlace).toBe('北京市')
    expect(wrapper.text()).toContain('重新排盘')
  })

  it('updates the existing record when submitting an edit draft', async () => {
    useAuthStore().user = loggedInUser
    vi.mocked(updateRecord).mockResolvedValue({ id: 7 } as never)
    useChartStore().setEditDraft({
      recordId: 7,
      input: {
        gender: 'M',
        calendar: 'solar',
        birth_date: '1990-05-20',
        birth_time: '10:30',
      },
      meta: { person_name: '儿子', relationship: 'CHILD', notes: '备注' },
    })
    const wrapper = mount(Home)
    await wrapper.find('button').trigger('click')
    await flush()
    expect(predictChart).not.toHaveBeenCalled()
    expect(updateRecord).toHaveBeenCalledTimes(1)
    const [id, payload] = vi.mocked(updateRecord).mock.calls[0] as [
      number,
      { person_name?: string; relationship?: string; notes?: string; birth_date?: string },
    ]
    expect(id).toBe(7)
    expect(payload.birth_date).toBe('1990-05-20')
    expect(payload.person_name).toBe('儿子')
    expect(payload.relationship).toBe('CHILD')
    expect(payload.notes).toBe('备注')
    expect(replace).toHaveBeenCalledWith('/records/7')
    expect(useChartStore().editDraft).toBeNull()
  })

  it('treats a draft without recordId as a fresh chart', async () => {
    useAuthStore().user = loggedInUser
    vi.mocked(saveRecord).mockResolvedValue({
      id: 1,
      chart_result: { day_master: '乙' },
    } as never)
    useChartStore().setEditDraft({
      recordId: null,
      input: { gender: 'M', calendar: 'solar', birth_date: '1990-05-20', birth_time: '10:30' },
    })
    const wrapper = mount(Home)
    await wrapper.find('button').trigger('click')
    await flush()
    expect(updateRecord).not.toHaveBeenCalled()
    expect(saveRecord).toHaveBeenCalledTimes(1)
    expect(push).toHaveBeenCalledWith('/result')
    expect(useChartStore().editDraft).toBeNull()
  })

  // ---------- 排盘自动保存 ----------

  it('auto-saves via saveRecord when logged in', async () => {
    useAuthStore().user = loggedInUser
    vi.mocked(saveRecord).mockResolvedValue({
      id: 99,
      person_name: null,
      relationship: 'SELF',
      created_at: '2026-08-12T00:00:00',
      chart_result: { day_master: '乙' },
    } as never)
    const wrapper = mount(Home)
    await wrapper.find('button').trigger('click')
    await flush()
    expect(predictChart).not.toHaveBeenCalled()
    expect(saveRecord).toHaveBeenCalledTimes(1)
    expect(push).toHaveBeenCalledWith('/result')
    expect(useChartStore().savedRecord).toEqual({
      id: 99,
      person_name: null,
      relationship: 'SELF',
      notes: null,
    })
  })

  it('falls back to predict when auto-save fails but still shows the chart', async () => {
    useAuthStore().user = loggedInUser
    vi.mocked(saveRecord).mockRejectedValue(new Error('保存失败'))
    vi.mocked(predictChart).mockResolvedValue({ day_master: '乙' } as never)
    const wrapper = mount(Home)
    await wrapper.find('button').trigger('click')
    await flush()
    expect(saveRecord).toHaveBeenCalledTimes(1)
    expect(predictChart).toHaveBeenCalledTimes(1)
    expect(push).toHaveBeenCalledWith('/result')
    expect(useChartStore().savedRecord).toBeNull()
  })
})
