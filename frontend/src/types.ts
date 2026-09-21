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

// ============================================================
// 012 期 v2 结论契约（engine === 'wangdu-v2'）
// ============================================================
// **独立设计、不与旧契约耦合**（spec FR-053）——字段名与嵌套均与 `WangduVerdict`
// 不同，展示层按 `engine` 分流（FR-054）。data-model.md §1 为准。
//
// 排盘字段（pillars / lunar_birth 等）**不属于本契约**，一律不变。

export interface V2RelationEffect {
  zhi: string
  gan?: string
  wuxing?: string
  delta?: number
  scale?: number
  remove?: boolean
  reason: string
}

export interface V2Relation {
  tier: number          // 1..18，对应十八级先后顺序
  type: string
  members: string[]
  cols: string[]
  hua: string | null
  detail: string
  effects: V2RelationEffect[]
  reason?: string       // rejected 时的不成立原因
  blocked_by?: { tier: number; type: string; cols: string[] } | null
}

export interface V2Degrees {
  base: number
  after_relations: number
  root: number
  static: number
  final: number
  coef: number
  state: string
}

export interface V2GeJu {
  type: 'zheng' | 'cong_ruo' | 'cong_qiang' | 'cong_yin' | 'cong_sha' | 'cong_cai' | 'hua'
  hua_shen: string | null
  cong_targets: string[]
  neng_duli: boolean
  liang_qi: string[] | null
  basis: string[]
}

export interface V2YongShenBlock {
  element: string | null
  basis: string
  direction?: string
  reason?: string
}

export interface V2Tiaohou {
  element: string | null
  basis: string
  met: boolean
  quantified: string
  position: string | null
}

export interface V2YongShen {
  empty: boolean
  theoretical: V2YongShenBlock | null
  practical: V2YongShenBlock | null
  tiaohou: V2Tiaohou | null
  xi_shen: string[]
  ji_shen: string[]
  xian_shen: string[]
  /** 第一/第二/第三用神（FR-039）。**刻度未定**，见下。 */
  tier: { first: string | null; second: string | null; third: string | null }
  direction: string | null
  basis: string
  /** 旬空标注：**无削弱系数**（书中无量化）。只标「逢旬空·受制」。 */
  xunkong?: { kong: string[]; notes: string[] }
}

export interface V2Layers {
  /** 层次等级刻度**属书中未量化项**，须 C26-n 裁定；裁定前恒为空串。 */
  verdict: string
  met: string[]
  missing: string[]
  penalties: { reason: string; delta: string }[]
  basis: string
}

/** 藏干在**该段结束时**的度数，以及它相对**原始藏干表**的变化。 */
export interface V2ChartHidden {
  gan: string
  wx: string
  degree: number
  /** 相对原始表的变化；第 1 段（原局）恒为 null。 */
  change: '新增' | '归零' | '增力' | '减力' | '变纯' | null
}

export interface V2ChartPillar {
  key: string
  label: string
  /** 该天干在**本段**的字——天干五合合化成功后会换成化神干支（甲→戊）。 */
  gan: string
  gan_wx: string
  /** 换字前的原局那个字；未参与合化换字时为 null。 */
  gan_original: string | null
  /** 本段该天干发生了什么：合化换字 / 合而不化的合绊减力；无则为 null。 */
  gan_change: '合化' | '合绊' | null
  /** 第 1–3 段为**该字自身**的生度数（原局 1）；
   *  第 4 段（通根递减）起改为该字所在**连片组的旺度**——生克算式里真正用的那个数（含通根）。
   *  2026-09-16 段序：五合排在第 6 段（静态旺度之后）。 */
  gan_degree: number
  /** 该字自身的旺度（生度数 × 月令系数）；第 4 段起才有，否则为 null。 */
  gan_own?: number | null
  /** 该字所在组的**根**（= `gan_degree` − `gan_own`）；第 4 段起才有，否则为 null。 */
  gan_root?: number | null
  zhi: string
  zhi_wx: string
  /** 该支**实际承载**的五行——合化变纯后已非本气五行，据此上色。 */
  zhi_effective_wx: string
  hidden: V2ChartHidden[]
  /** 整支变纯时的说明（含原来的字）；否则为 null。 */
  note: string | null
}

/** 某一段**结束时**的命盘快照（第 1–8 段；格局/取用段不改度数，故不带）。 */
export interface V2StepChart {
  pillars: V2ChartPillar[]
}

/** 结算过程中的一张快照（生克结算段「每一柱计算完成显示当前命盘」）。
 *
 *  `after` = 该实例结算完时依据行已产出的条数，前端据此把图插在对应算式之后。 */
export interface V2StepChartPoint {
  label: string
  after: number
  chart: V2StepChart
}

export interface V2Step {
  key: string
  title: string
  rule: string
  /** 该段生效的**口径裁定编号**（C26-n / O-n），可在 research.md 定位（FR-056）。 */
  rulings?: string[]
  /** 该段结束时的命盘快照——第 1–8 段有，第 9/10 段（格局/取用）无。 */
  chart?: V2StepChart
  /** 结算过程中的逐实例快照（仅生克结算段）。有它时前端不再重复贴段末那张。 */
  charts?: V2StepChartPoint[]
  traces: StepTrace[]
  result: string
}

export interface V2DayunStep {
  /** 来源阶段（013 FR-024）——阶段 2 为 `"dayun"`，阶段 3 为 `"liunian"`。 */
  source?: 'dayun' | 'liunian'
  ganzhi: string
  /** 阶段 3 才有：该年流年干支。 */
  liunian?: string | null
  start_year: number | null
  start_age_xu: number | null
  level: string
  ge_ju: V2GeJu
  yong_shen: V2YongShen
  /** 该步的**关系裁定**——已把本步干支并入判定（FR-042 的大运维度）。 */
  relations: { established: V2Relation[]; rejected: V2Relation[] }
  transition: '成格' | '破格' | null
  deltas: StepTrace[]
  scores_after: Record<string, number>
  /** 该步的调候量化（013 T035；FR-021b）——按该步同口径重判。 */
  tiaohou?: V2Tiaohou | null
  /** 该步的格局层次（013 T035；FR-021b）——按该步同口径重判。 */
  layers?: V2Layers | null
  /** 该阶段的判定依据段（data-model §1）——逐段可读，供页面「依据可追溯」用。 */
  steps?: V2Step[]
}

/** 成对呈现的一侧：值 + 来源阶段（013 FR-016c / FR-024）。 */
export interface V2PairSide {
  value: unknown
  source: 'dayun' | 'liunian'
}

/** 「加入流年」页的**同名判断成对**条目（013 FR-016c / SC-009）。
 *
 *  `changed` 只提示两侧取值不同，**不是吉凶结论**（FR-016a）。 */
export interface V2Pair {
  key: string
  label: string
  dayun: V2PairSide
  liunian: V2PairSide
  changed: boolean
}

/** `POST /api/charts/suiyun` 与 `GET /api/records/{id}/suiyun` 的响应
 *  （013 T034；contracts/suiyun-v2.md §2）。**按需实时算、不落库**（FR-026）。 */
export interface SuiyunResponse {
  engine: 'wangdu-v2'
  contract_version: number
  /** 2 = 只加了大运；3 = 另加流年（`liunian`/`pairs` 非空）。 */
  stage: 2 | 3
  input_scope?: 'four_pillars' | 'three_pillars'
  /** 该盘在岁运阶段的降级说明（FR-025）；无降级时为空数组。 */
  degradations: string[]
  dayun: V2DayunStep
  liunian: V2DayunStep | null
  pairs: V2Pair[] | null
}

/** 012 期 v2 结论（engine === 'wangdu-v2'）。 */
export interface WangduV2 {
  engine: 'wangdu-v2'
  contract_version: 2
  /** **换字后**的日干——日干参与天干五合且化成功时已改宗（甲→戊），否则即原字。 */
  day_master: string
  /** 原局的日干字；未换字时与 `day_master` 相同。 */
  day_master_original?: string
  day_master_wuxing: string
  input_scope: 'four_pillars' | 'three_pillars'
  degradations: string[]
  relations: { established: V2Relation[]; rejected: V2Relation[] }
  degrees: Record<string, V2Degrees>
  level: string
  ge_ju: V2GeJu
  yong_shen: V2YongShen
  layers?: V2Layers
  steps: V2Step[]
  dayun: V2DayunStep[]
}

export function isWangduV2(s: unknown): s is WangduV2 {
  return !!s && typeof s === 'object' && (s as { engine?: string }).engine === 'wangdu-v2'
}
