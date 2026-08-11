import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import type { ShichenMoments, ShichenSegment } from '../src/types'

import ShichenDial from '../src/components/ShichenDial.vue'

// 24 段、每段 1 小时，自 2020-06-21T00:00 起（便于角度断言）
const mkSegments = (firstLenHours = 1): ShichenSegment[] => {
  const order = ['卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑', '寅']
  const base = new Date('2020-06-21T00:00:00').getTime()
  const starts: number[] = [base]
  for (let i = 0; i < 24; i++) {
    const len = i === 0 ? firstLenHours : 1
    starts.push(starts[i] + len * 3600_000)
  }
  return Array.from({ length: 24 }, (_, i) => ({
    index: i,
    start: new Date(starts[i]).toISOString(),
    end: new Date(starts[i + 1]).toISOString(),
    shichen: order[Math.floor(((i + 1) % 24) / 2)],
    alt_start: null,
    alt_end: null,
  }))
}

const mkMoments = (segments: ShichenSegment[]): ShichenMoments => ({
  sunrise: segments[2].start,
  sunset: segments[14].start,
  solar_noon: segments[8].start, // 第 8 段起点视为正午（top 对齐基准）
  solar_midnight: segments[20].start,
  prev_sunrise: null,
  prev_noon: segments[8].start,
  prev_sunset: null,
  next_sunrise: null,
})

const mountDial = (segments: ShichenSegment[], birthTime: string | null) =>
  mount(ShichenDial, {
    props: {
      moments: mkMoments(segments),
      segments,
      birthTime,
      birthSegment: birthTime ? 6 : null,
    },
  })

describe('ShichenDial', () => {
  it('renders 24 sectors with sweep angles proportional to duration', () => {
    const segments = mkSegments(2) // 第 0 段 2 小时，其余 1 小时
    const wrapper = mountDial(segments, null)
    const sectors = wrapper.findAll('path.seg-sector')
    expect(sectors).toHaveLength(24)
    const sweeps = sectors.map((s) => Number(s.attributes('data-sweep')))
    const total = sweeps.reduce((a, b) => a + b, 0)
    expect(total).toBeCloseTo(360, 3)
    expect(sweeps[0]).toBeCloseTo(sweeps[1] * 2, 3) // 角度与时长成比例
  })

  it('marks the four key solar moments', () => {
    const wrapper = mountDial(mkSegments(), null)
    for (const cls of ['marker-sunrise', 'marker-noon', 'marker-sunset', 'marker-midnight']) {
      expect(wrapper.find(`.${cls}`).exists()).toBe(true)
    }
  })

  it('places the birth pointer at the angle of the birth time', () => {
    const segments = mkSegments()
    // 正午 = segments[8].start（08:00）对齐正上方；出生 10:00 = 窗口 10/24 处
    const wrapper = mountDial(segments, segments[10].start)
    const pointer = wrapper.find('line.birth-pointer')
    expect(pointer.exists()).toBe(true)
    const raw = (10 / 24) * 360 // 150°
    const expected = Number((raw - (8 / 24) * 360 - 90).toFixed(4)) // 相对正午对齐并转到顶部 = -60°
    expect(pointer.attributes('transform')).toContain(`rotate(${expected}`)
  })

  it('labels all 12 shichen around the dial', () => {
    const wrapper = mountDial(mkSegments(), null)
    const labels = wrapper.findAll('text.shichen-label')
    expect(labels).toHaveLength(12)
    expect(labels.map((l) => l.text())).toEqual([
      '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑', '寅',
    ])
  })

  it('omits the birth pointer when birth time is unknown', () => {
    const wrapper = mountDial(mkSegments(), null)
    expect(wrapper.find('line.birth-pointer').exists()).toBe(false)
  })
})
