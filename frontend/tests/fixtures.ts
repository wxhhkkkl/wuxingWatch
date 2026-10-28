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
  wan_du: {
    engine: 'wangdu-v2',
    contract_version: 2,
    day_master: '乙',
    day_master_original: '乙',
    day_master_wuxing: '木',
    input_scope: 'four_pillars',
    degradations: [],
    relations: { established: [], rejected: [] },
    degrees: {
      木: { base: 4, after_relations: 4, root: 2, static: 4, final: 6, coef: 1, state: '旺' },
      火: { base: 1, after_relations: 1, root: 1, static: 1, final: 1, coef: 1, state: '相' },
      土: { base: 1, after_relations: 1, root: 1, static: 1, final: 1, coef: 1, state: '休' },
      金: { base: 3, after_relations: 3, root: 2, static: 3, final: 3, coef: 1, state: '囚' },
      水: { base: 1, after_relations: 1, root: 1, static: 1, final: 1, coef: 1, state: '死' },
    },
    static_scores: { 木: 4, 火: 1, 土: 1, 金: 3, 水: 1 },
    final_scores: { 木: 6, 火: 1, 土: 1, 金: 3, 水: 1 },
    level: '偏弱',
    stem_groups: [],
    day_master_group: null,
    benqi_instances: [],
    steps: [
      {
        key: 'relations',
        title: '第 1 段 · 关系判定',
        rule: '按十八级顺序逐级判定',
        rulings: ['O-5（严格让位）'],
        traces: [{ target: '', expression: '六冲成立：子午冲', value: null }],
        result: '成立 1 条、让位 0 条',
      },
      {
        key: 'total',
        title: '第 8 段 · 动态旺度与定级',
        rule: '按十一档定级',
        traces: [
          { target: '木', expression: '木：动态旺度 6 度', value: 6 },
          { target: '金', expression: '金：动态旺度 3 度', value: 3 },
        ],
        result: '日主 乙（木）6 度 → 偏弱',
      },
    ],
  },
  missing_parts: [],
}
