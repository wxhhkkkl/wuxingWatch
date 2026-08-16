import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { mockResult, mockInputs } from './fixtures'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push, replace: vi.fn() }),
}))

vi.mock('../src/api/records', () => ({ saveRecord: vi.fn(), updateRecord: vi.fn() }))
vi.mock('../src/api/charts', () => ({ fetchChartImage: vi.fn(), fetchLiuShi: vi.fn() }))

import { useChartStore } from '../src/stores/chart'
import { useAuthStore } from '../src/stores/auth'
import { fetchLiuShi } from '../src/api/charts'
import { saveRecord, updateRecord } from '../src/api/records'
import ChartResult from '../src/pages/ChartResult.vue'

describe('ChartResult', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    push.mockClear()
    vi.mocked(saveRecord).mockReset()
    vi.mocked(updateRecord).mockReset()
  })

  it('renders chart sections when a result exists', () => {
    useChartStore().set(mockResult, mockInputs)
    const wrapper = mount(ChartResult)
    expect(wrapper.text()).toContain('四柱')
    expect(wrapper.text()).toContain('喜忌分析')
    expect(wrapper.text()).toContain('庚') // 年柱天干（明细表格分列渲染）
    expect(wrapper.text()).toContain('身强')
  })

  it('renders the 命盘图 relation diagram card with tabs', async () => {
    useChartStore().set(mockResult, mockInputs)
    const wrapper = mount(ChartResult)
    expect(wrapper.text()).toContain('命盘图')
    expect(wrapper.find('[data-testid="relation-diagram"]').exists()).toBe(true)
    // 默认关系 tab：SVG 连线图节点（年柱天干庚）
    expect(wrapper.find('[data-testid="node-gan-year"]').text()).toBe('庚')
    // 切到宫位 tab：显示配偶宫
    await wrapper.find('[data-testid="tab-gongwei"]').trigger('click')
    expect(wrapper.find('[data-testid="palace-day"]').text()).toBe('配偶宫')
  })

  it('shows an empty state when no result', () => {
    const wrapper = mount(ChartResult)
    expect(wrapper.text()).toContain('暂无排盘结果')
  })

  it('redirects to login when saving while logged out', async () => {
    useChartStore().set(mockResult, mockInputs)
    expect(useAuthStore().isLoggedIn).toBe(false)
    const wrapper = mount(ChartResult)
    const saveButton = wrapper.findAll('button').find((b) => b.text().includes('保存记录'))
    await saveButton!.trigger('click')
    expect(push).toHaveBeenCalledWith('/login')
  })

  it('真太阳时 row is clickable only when precise shichen applied', async () => {
    // 未开启精确时辰：不可点
    useChartStore().set(mockResult, mockInputs) // mockResult 无 shichen
    const wrapper = mount(ChartResult)
    const row = wrapper.find('[data-testid="row-true-solar"]')
    expect(row.classes()).not.toContain('is-link')
    await row.trigger('click')
    expect(push).not.toHaveBeenCalledWith('/shichen')

    // 开启后可点击跳转
    const withShichen = {
      ...mockResult,
      shichen: { applied: true, shichen: '巳', traditional_shichen: '巳' },
    } as never
    useChartStore().set(withShichen, mockInputs)
    const wrapper2 = mount(ChartResult)
    const row2 = wrapper2.find('[data-testid="row-true-solar"]')
    expect(row2.classes()).toContain('is-link')
    await row2.trigger('click')
    expect(push).toHaveBeenCalledWith('/shichen')
  })

  it('shows 出生节气/星座/星宿 rows when present, omits otherwise', () => {
    useChartStore().set(mockResult, mockInputs)
    const wrapper = mount(ChartResult)
    expect(wrapper.text()).not.toContain('出生节气')

    const withJieqi = {
      ...mockResult,
      jieqi: {
        prev: { name: '惊蛰', time: '1990-03-06T04:19:18', days: 25, hours: 19 },
        next: { name: '清明', time: '1990-04-05T09:12:56', days: 4, hours: 9 },
      },
      xing_zuo: '白羊座',
      xing_xiu: '虚宿北方玄武',
    } as never
    useChartStore().set(withJieqi, mockInputs)
    const wrapper2 = mount(ChartResult)
    expect(wrapper2.text()).toContain('出生于惊蛰后')
    expect(wrapper2.text()).toContain('清明前')
    expect(wrapper2.text()).toContain('白羊座')
    expect(wrapper2.text()).toContain('虚宿北方玄武')
    // 日出日落行已移除
    expect(wrapper2.text()).not.toContain('日出')
  })

  it('shows 旺相休囚死 row only when wang_xiang present', () => {
    // 旧记录无 wang_xiang：行不渲染
    useChartStore().set(mockResult, mockInputs)
    const wrapper = mount(ChartResult)
    expect(wrapper.find('[data-testid="row-wang-xiang"]').exists()).toBe(false)

    const withWx = {
      ...mockResult,
      hidden_stems: {
        ...mockResult.hidden_stems,
        wang_xiang: { 旺: '火', 相: '土', 休: '木', 囚: '水', 死: '金' },
      },
    } as never
    useChartStore().set(withWx, mockInputs)
    const wrapper2 = mount(ChartResult)
    const row = wrapper2.find('[data-testid="row-wang-xiang"]')
    expect(row.exists()).toBe(true)
    expect(row.text()).toContain('旺火')
    expect(row.text()).toContain('死金')
  })

  it('cascades 流年→流月→流日→流时 with on-demand fetches and table columns', async () => {
    const curYear = new Date().getFullYear()
    const now = new Date()
    const p = (n: number) => String(n).padStart(2, '0')
    const today = `${now.getFullYear()}-${p(now.getMonth() + 1)}-${p(now.getDate())}`
    const mkLn = (y: number) => ({
      year: y, gan: '丙', zhi: '午', ganzhi: '丙午', gan_shishen: '七杀', zhi_shishen: '正官',
    })
    const cascadeResult = {
      ...mockResult,
      da_yun: {
        start_age: 5,
        start_month: 7,
        steps: [{
          ganzhi: '甲辰', start_year: curYear, end_year: curYear + 9,
          gan: '甲', zhi: '辰', gan_shishen: '偏财', zhi_shishen: '偏印',
          liu_nian: Array.from({ length: 10 }, (_, i) => mkLn(curYear + i)),
        }],
      },
    } as never

    const ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    vi.mocked(fetchLiuShi).mockImplementation(((input: { level: string }) => {
      if (input.level === 'month') {
        return Promise.resolve({
          year: curYear,
          year_ganzhi: '丙午',
          months: [{
            branch: '寅', label: '寅月', ganzhi: '庚寅', gan: '庚', zhi: '寅',
            gan_shishen: '比肩', zhi_shishen: '偏财',
            start: '2000-01-01T00:00:00', end: '2099-12-31T00:00:00', // 覆盖今天 → 自动选中
          }],
        })
      }
      if (input.level === 'day') {
        return Promise.resolve({
          month_branch: '寅',
          month_ganzhi: '庚寅',
          days: [{ date: today, ganzhi: '己酉', gan: '己', zhi: '酉', gan_shishen: '正印', hours: [] }],
        })
      }
      return Promise.resolve({
        date: today,
        day_ganzhi: '己酉',
        hours: ZHI.map((z) => ({ zhi: z, ganzhi: `甲${z}`, gan_shishen: '偏财' })),
      })
    }) as never)

    useChartStore().set(cascadeResult, mockInputs)
    const wrapper = mount(ChartResult)
    // 级联三级各一次 fetch，逐轮 flush
    await flushPromises()
    await flushPromises()
    await flushPromises()
    await flushPromises()

    const calls = vi.mocked(fetchLiuShi).mock.calls.map((c) => c[0]) as {
      level: string; year: number; month_branch?: string; date?: string
      context: { day_ganzhi: string; year_ganzhi: string; month_zhi: string }
    }[]
    expect(calls[0]).toEqual({
      level: 'month', year: curYear,
      context: { day_ganzhi: '乙酉', year_ganzhi: '庚午', month_zhi: '巳' },
    })
    expect(calls[1]).toMatchObject({ level: 'day', year: curYear, month_branch: '寅' })
    expect(calls[2]).toMatchObject({ level: 'hour', year: curYear, month_branch: '寅', date: today })

    // 明细表 9 列：流时/流日/流月/流年/大运 + 四柱
    const headers = wrapper.findAll('.pt-col-header').map((h) => h.text())
    expect(headers).toEqual(['流时', '流日', '流月', '流年', '大运', '年柱', '月柱', '日柱', '时柱'])
    expect(wrapper.find('[data-testid="gan-liuyue"]').text()).toBe('庚')

    // 显隐开关：取消勾选后隐藏流月/流日/流时三列（横条联动不受影响）
    const toggle = wrapper.find('[data-testid="toggle-liu-cols"] input')
    expect(toggle.exists()).toBe(true)
    await toggle.setValue(false)
    const headers2 = wrapper.findAll('.pt-col-header').map((h) => h.text())
    expect(headers2).toEqual(['流年', '大运', '年柱', '月柱', '日柱', '时柱'])
    expect(wrapper.findAll('.fs-liuyue-item').length).toBe(1) // 横条仍在
    await toggle.setValue(true)
    expect(wrapper.findAll('.pt-col-header').length).toBe(9) // 再勾选恢复
  })

  it('edits an auto-saved record (PUT) with pre-filled info', async () => {
    useAuthStore().user = { id: 1, phone: '13800000000' }
    useChartStore().set(mockResult, mockInputs)
    useChartStore().setSavedRecord({ id: 5, person_name: '儿子', relationship: 'CHILD', notes: '备注' })
    vi.mocked(updateRecord).mockResolvedValue({ id: 5 } as never)
    const wrapper = mount(ChartResult)

    const editBtn = wrapper.findAll('button').find((b) => b.text().includes('编辑信息'))
    expect(editBtn).toBeDefined()
    await editBtn!.trigger('click')

    // 弹窗预填人物/关系/备注（van-field 值在 input.value 中，非文本）
    expect(wrapper.text()).toContain('编辑排盘信息')
    const fieldValues = wrapper.findAll('input').map((i) => (i.element as HTMLInputElement).value)
    expect(fieldValues).toContain('儿子')
    expect(fieldValues).toContain('备注')

    await wrapper.findAll('button').find((b) => b.text().includes('确认保存'))!.trigger('click')
    await flushPromises()

    expect(updateRecord).toHaveBeenCalledTimes(1)
    const [id, payload] = vi.mocked(updateRecord).mock.calls[0] as [
      number,
      { person_name?: string; relationship?: string; notes?: string },
    ]
    expect(id).toBe(5)
    expect(payload.person_name).toBe('儿子')
    expect(payload.relationship).toBe('CHILD')
    expect(payload.notes).toBe('备注')
    // store 元信息回写
    expect(useChartStore().savedRecord).toEqual({
      id: 5,
      person_name: '儿子',
      relationship: 'CHILD',
      notes: '备注',
    })
  })

  it('shows wangdu conclusion with dual yongshen and clickable 查看计算过程 entry', async () => {
    const withWangdu = {
      ...mockResult,
      xi_yong: {
        ...mockResult.xi_yong,
        conclusion: {
          yong_shen: '金',
          tiaohou_yong_shen: { element: '火', basis: '生于丑月，寒湿需火调候' },
          xi_shen: ['土'],
          ji_shen: ['木', '水'],
          summary: '较弱·正格',
          basis: { yong_shen: '身弱取生扶', tiaohou: '丑月需火' },
        },
        strength: {
          method: 'sizhu-jingsui',
          level: '较弱',
          day_master: '庚',
          day_master_wuxing: '金',
          static_scores: { 木: 4.55, 火: 5.6, 土: 18, 金: 4.5, 水: 3.2 },
          final_scores: { 木: 4.55, 火: 4.0, 土: 18, 金: 4.5, 水: 3.2 },
          ge_ju: { type: 'zheng', hua_shen: null, basis: ['日主庚金 4.5 度'], neng_duli: true },
          steps: [
            { key: 'static', title: '静态旺度', rule: 'r', traces: [{ target: '金', expression: '庚1+丑辛2', value: 3 }], result: '金 4.5' },
          ],
          dayun_adjustments: [],
        },
      },
    } as never
    useChartStore().set(withWangdu, mockInputs)
    const wrapper = mount(ChartResult)
    // 双用神并列：格局用神 + 调候用神
    expect(wrapper.text()).toContain('用神')
    expect(wrapper.text()).toContain('调候')
    expect(wrapper.text()).toContain('较弱·正格')
    // 查看计算过程入口 → /strength
    const link = wrapper.find('[data-testid="strength-link"]')
    expect(link.exists()).toBe(true)
    expect(link.text()).toContain('较弱')
    await link.trigger('click')
    expect(push).toHaveBeenCalledWith('/strength')
  })

  it('shows legacy hint and hides 计算过程 entry for old-format strength records', () => {
    const withLegacy = {
      ...mockResult,
      xi_yong: {
        ...mockResult.xi_yong,
        strength: {
          level: '偏旺', classification: '身强', cong_ge: false,
          day_master: '乙', day_master_wuxing: '木', day_master_score: 132.4, balance_line: 109,
          scores: { 木: 132.4, 火: 98.2, 土: 120.1, 金: 95.3, 水: 98.0 },
          steps: [{ title: '天干基础分', description: 'd', values: { 木: 72 } }],
        },
      },
    } as never
    useChartStore().set(withLegacy, mockInputs)
    const wrapper = mount(ChartResult)
    expect(wrapper.find('[data-testid="strength-link"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('旧版口径')
  })

  it('falls back to summary and hides strength link for old records', () => {
    useChartStore().set(mockResult, mockInputs) // mockResult 无 strength
    const wrapper = mount(ChartResult)
    expect(wrapper.find('[data-testid="strength-link"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('喜忌分析')
    expect(wrapper.text()).toContain('身强') // conclusion.summary 回退
  })
})
