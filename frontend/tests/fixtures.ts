import type { BirthInput, ChartResult } from '../src/types'

export const mockInputs: BirthInput = {
  gender: 'M',
  calendar: 'solar',
  birth_date: '1990-05-20',
  birth_time: '10:30',
  birth_place: '北京市',
}

const pillar = (ganzhi: string, gan: string, zhi: string, shishen: string) => ({
  ganzhi,
  gan,
  zhi,
  gan_wuxing: '木',
  zhi_wuxing: '金',
  shishen,
})

export const mockResult: ChartResult = {
  solar_birth: '1990-05-20T10:30:00',
  true_solar_time: '1990-05-20T10:15:00',
  lunar_birth: '一九九〇年四月廿六',
  pillars: {
    year: pillar('庚午', '庚', '午', '正官'),
    month: pillar('辛巳', '辛', '巳', '七杀'),
    day: pillar('乙酉', '乙', '酉', '日主'),
    time: pillar('辛巳', '辛', '巳', '七杀'),
  },
  day_master: '乙',
  hidden_stems: { branch: '巳', hidden_stems: ['丙', '庚', '戊'], ruling_stem: '丙', source: '《子平真诠》司权天数表' },
  tai_yuan: '壬申',
  ming_gong: '癸未',
  shen_gong: '丁亥',
  da_yun: { start_age: 5, start_month: 7, steps: [{ ganzhi: '壬午', start_year: 1995, end_year: 2004 }] },
  liu_nian: [{ year: 2026, ganzhi: '丙午' }],
  xi_yong: {
    conclusion: { yong_shen: '火', xi_shen: ['土'], ji_shen: ['木'], summary: '身强' },
    favorable_elements: ['火', '土'],
    avoid_elements: ['木'],
    reasoning: '日主乙属木，命局判定为「身强」。',
    ten_gods: { year: '正官' },
    direction: { career: '以稳健为主', fortune: '注意控制消费', health: {}, note: '参考信息' },
    disclaimer: '内容为算法生成的参考信息，仅供参考',
  },
  missing_parts: [],
}
