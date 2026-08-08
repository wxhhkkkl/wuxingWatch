export interface Pillar {
  ganzhi: string
  gan: string
  zhi: string
  gan_wuxing: string
  zhi_wuxing: string
  shishen: string
}

export interface DaYunStep {
  ganzhi: string
  start_year: number | null
  end_year: number | null
}

export interface LiuNian {
  year: number
  ganzhi: string
}

export interface XiYongConclusion {
  yong_shen: string
  xi_shen: string[]
  ji_shen: string[]
  summary: string
}

export interface XiYong {
  conclusion: XiYongConclusion
  favorable_elements: string[]
  avoid_elements: string[]
  reasoning: string
  ten_gods: Record<string, string>
  direction: Record<string, unknown>
  disclaimer: string
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
  hidden_stems: { branch: string; hidden_stems: string[]; ruling_stem: string; source: string }
  tai_yuan: string
  ming_gong: string | null
  shen_gong: string | null
  da_yun: { start_age: number | null; start_month: number | null; steps: DaYunStep[] }
  liu_nian: LiuNian[]
  xi_yong: XiYong
  missing_parts: string[]
  note?: string
}

export interface User {
  id: number
  phone: string
  name?: string | null
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
  birth_pillars?: { year: string; month: string; day: string; time: string }
}
