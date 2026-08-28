export interface Pillar {
  ganzhi: string
  gan: string
  zhi: string
  gan_wuxing: string
  zhi_wuxing: string
  shishen: string
  detail?: PillarDetail
}

export interface CangGan {
  gan: string
  shishen: string
}

export interface PillarDetail {
  gan_shishen: string
  zhi_shishen: string
  cang_gan: CangGan[]
  xing_yun: string
  zi_zuo: string
  xun_kong: string
  na_yin: string
  shen_sha: string[]
}

export interface LiuNianStep {
  year: number
  gan: string
  zhi: string
  ganzhi: string
  gan_shishen: string
  zhi_shishen: string
  detail?: PillarDetail
}

export interface DaYunStep {
  ganzhi: string
  start_year: number | null
  end_year: number | null
  gan?: string
  zhi?: string
  gan_shishen?: string
  zhi_shishen?: string
  start_age_xu?: number | null
  detail?: PillarDetail
  liu_nian?: LiuNianStep[] | null
}

export interface LiuNian {
  year: number
  ganzhi: string
}

/** 流月（节气月）条目 — POST /api/charts/liushi level=month */
export interface LiuYueItem {
  branch: string
  label: string
  ganzhi: string
  gan: string
  zhi: string
  gan_shishen: string
  zhi_shishen: string
  detail?: PillarDetail
  start: string
  end: string
}

/** 流时轻量条目（流日内嵌，无 detail） */
export interface LiuShiLight {
  zhi: string
  ganzhi: string
  gan_shishen: string
}

/** 流日条目 — level=day */
export interface LiuRiItem {
  date: string
  ganzhi: string
  gan: string
  zhi: string
  gan_shishen: string
  detail?: PillarDetail
  hours: LiuShiLight[]
}

/** 流时条目（含 detail） — level=hour */
export interface LiuShiItem extends LiuShiLight {
  detail?: PillarDetail
}

export interface LiuShiContext {
  day_ganzhi: string
  year_ganzhi: string
  month_zhi: string
}

export interface LiuShiRequest {
  level: 'month' | 'day' | 'hour'
  year: number
  month_branch?: string
  date?: string
  context: LiuShiContext
}

export interface LiuYueResponse {
  year: number
  year_ganzhi: string
  months: LiuYueItem[]
}

export interface LiuRiResponse {
  month_branch: string
  month_ganzhi: string
  days: LiuRiItem[]
}

export interface LiuShiResponse {
  date: string
  day_ganzhi: string
  hours: LiuShiItem[]
}

export interface TiaohouYongShen {
  element: string | null
  basis: string
}

export interface XiYongConclusion {
  yong_shen: string
  tiaohou_yong_shen?: TiaohouYongShen
  xi_shen: string[]
  ji_shen: string[]
  summary: string
  basis?: { yong_shen: string; tiaohou: string }
}

export interface StrengthScoreStep {
  title: string
  description: string
  values?: Record<string, number>
}

/** 005 期旧评分法形状（旧记录）；008 起由 WangduVerdict 取代。 */
export interface LegacyStrengthVerdict {
  level: string
  classification: '身强' | '身弱' | '中和' | '从格'
  cong_ge: boolean
  day_master: string
  day_master_wuxing: string
  day_master_score: number
  balance_line: number
  scores: Record<string, number>
  steps: StrengthScoreStep[]
  method?: undefined
}

export interface StepTrace {
  target: string
  expression: string
  value: number | string | null
}

export interface WangduStep {
  // 010 定性 1-5 → 定量 6-11 → 下游沿用（14 键，废弃 static/dynamic_a/dynamic_b/final）
  key: 'month_hua' | 'month_state' | 'branch_rel' | 'branch_root' | 'stem_hua'
    | 'base_score' | 'branch_effects' | 'tonggen' | 'month_coef' | 'stem_shengke' | 'total'
    | 'geju' | 'dayun' | 'yongshen'
  title: string
  rule: string
  traces: StepTrace[]
  result: string
}

export interface GeJuVerdict {
  type: 'zheng' | 'cong_ruo' | 'cong_qiang' | 'cong_yin' | 'cong_sha' | 'cong_cai' | 'hua'
  hua_shen: string | null
  basis: string[]
  neng_duli: boolean
}

export interface DayunAdjustment {
  ganzhi: string
  start_year: number | null
  start_age_xu: number | null
  deltas: StepTrace[]
  scores_after: Record<string, number>
  level_after: string
}

/** 008 期《四柱精髓》旺度法输出（method === 'sizhu-jingsui'）。 */
export interface WangduVerdict {
  method: 'sizhu-jingsui'
  level: string
  day_master: string
  day_master_wuxing: string
  static_scores: Record<string, number>
  final_scores: Record<string, number>
  ge_ju: GeJuVerdict
  steps: WangduStep[]
  dayun_adjustments: DayunAdjustment[]
}

export type StrengthVerdict = WangduVerdict | LegacyStrengthVerdict

export function isWangduStrength(s: StrengthVerdict | undefined | null): s is WangduVerdict {
  return !!s && s.method === 'sizhu-jingsui'
}

export interface XiYong {
  conclusion: XiYongConclusion
  favorable_elements: string[]
  avoid_elements: string[]
  reasoning: string
  ten_gods: Record<string, string>
  direction: Record<string, unknown>
  disclaimer: string
  strength?: StrengthVerdict
}

export interface ShichenMoments {
  sunrise: string | null
  sunset: string | null
  solar_noon: string
  solar_midnight: string
  prev_sunrise: string | null
  prev_noon: string
  prev_sunset: string | null
  next_sunrise: string | null
}

export interface ShichenSegment {
  index: number
  start: string
  end: string
  shichen: string
  alt_start: number | null
  alt_end: number | null
}

export interface ShichenDetail {
  applied: boolean
  fallback: boolean
  shichen: string
  traditional_shichen: string | null
  segment_index: number | null
  day_offset: number
  moments: ShichenMoments
  segments: ShichenSegment[]
}

export interface ChartResult {
  solar_birth: string
  true_solar_time: string
  lunar_birth: string
  pillars: {
    year: Pillar | null
    month: Pillar | null
    day: Pillar | null
    time: Pillar | null
  }
  day_master: string
  hidden_stems: {
    branch: string
    hidden_stems: string[]
    ruling_stem: string
    wang_xiang?: Record<'旺' | '相' | '休' | '囚' | '死', string>
    source: string
  }
  tai_yuan: string
  ming_gong: string | null
  shen_gong: string | null
  da_yun: {
    start_age: number | null
    start_month: number | null
    start_day?: number | null
    start_hour?: number | null
    jiao_yun?: {
      year_gan: string
      jie: string
      days: number
      hours: number
      first_year: number
    } | null
    steps: DaYunStep[]
  }
  liu_nian: LiuNian[]
  xi_yong: XiYong
  missing_parts: string[]
  note?: string
  birth_place?: string
  timezone?: string
  dst?: { in_dst: boolean; note: string; original_time: string; corrected_time: string } | null
  sun?: {
    sunrise: string | null
    sunset: string | null
    solar_noon: string
    solar_midnight: string
  } | null
  shichen?: ShichenDetail
  jieqi?: {
    prev: { name: string; time: string; days: number; hours: number }
    next: { name: string; time: string; days: number; hours: number }
  } | null
  xing_zuo?: string | null
  xing_xiu?: string | null
}

export interface User {
  id: number
  phone: string
  name?: string | null
  role?: string
}

// ---------- 阅读模块（006-reading-module） ----------

export interface Chapter {
  id: number
  book_id: number
  title: string
  content: string | null
  sort_order: number
}

export interface ReadingBook {
  id: number
  title: string
  author: string | null
  description: string | null
  cover_url: string | null
  category_id: number | null
  current_chapter_id: number | null
  chapters: Chapter[]
}

export interface ReadingChapterDetail {
  id: number
  book_id: number
  title: string
  content: string | null
  prev_chapter_id: number | null
  next_chapter_id: number | null
}

export interface ReadingCategory {
  id: number
  name: string
  book_count: number
}

export interface ReadingBookSummary {
  id: number
  title: string
  author: string | null
  description: string | null
  cover_url: string | null
  category_id: number | null
  chapter_count: number
}

export interface ReadingBookList {
  items: ReadingBookSummary[]
  total: number
  page: number
  page_size: number
}

export interface RecordSummary {
  id: number
  person_name: string | null
  relationship: string
  birth_solar: string
  created_at: string
  summary: {
    year?: Pillar | null
    month?: Pillar | null
    day?: Pillar | null
    time?: Pillar | null
  }
}

export interface RecordDetail {
  id: number
  person_name: string | null
  relationship: string
  notes: string | null
  created_at: string
  chart_result: ChartResult
  birth_input?: BirthInput
}

export interface BirthInput {
  name?: string
  gender: 'M' | 'F' | 'UNKNOWN'
  calendar: 'solar' | 'lunar' | 'sizhu'
  birth_date?: string
  birth_time?: string
  birth_month_is_leap?: boolean
  birth_place?: string
  longitude?: number
  latitude?: number
  timezone?: string
  birth_pillars?: { year: string; month: string; day: string; time: string }
  precise_shichen?: boolean
}
