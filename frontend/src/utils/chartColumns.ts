/**
 * 命盘板（`components/PillarBoard.vue`）的**列适配**：把三种来源的数据整成同一种列。
 *
 * 只有这里知道「四柱 / 大运 / 流年」三种形状的差别——组件只管画。岁运两页的列因此
 * 与原局页**长得一样**（干上支下 + 十神 + 藏干），不必各写一套模板。
 */
import type { CangGan, ChartResult, DaYunStep, LiuNianStep, Pillar } from '../types'
import { GAN_WUXING, ZHI_WUXING } from './wuxing'

/** 命盘板的一列。缺列（如阶段 2 的流年）时 `gan`/`zhi` 为空串、`dim` 为真。 */
export interface BoardColumn {
  key: string
  label: string
  gan: string
  gan_wx: string
  zhi: string
  zhi_wx: string
  shishen: string
  cang_gan: CangGan[]
  /** 该字**未参与**本阶段判定——灰显，且不画藏干。 */
  dim?: boolean
}

const PILLAR_LABEL = { year: '年', month: '月', day: '日', time: '时' } as const

/** 四柱四列（顺序固定；缺柱跳过——如时辰不详时无时柱）。 */
export function natalColumns(pillars: ChartResult['pillars'] | undefined): BoardColumn[] {
  if (!pillars) return []
  return (['year', 'month', 'day', 'time'] as const)
    .map((k) => {
      const p: Pillar | null = pillars[k]
      return p ? fromPillar(k, PILLAR_LABEL[k], p) : null
    })
    .filter((x): x is BoardColumn => x !== null)
}

function fromPillar(key: string, label: string, p: Pillar): BoardColumn {
  return {
    key, label,
    gan: p.gan, gan_wx: p.gan_wuxing,
    zhi: p.zhi, zhi_wx: p.zhi_wuxing,
    shishen: p.shishen ?? '',
    cang_gan: p.detail?.cang_gan ?? [],
  }
}

/** 一步大运 — 一列。 */
export function dayunColumn(step: DaYunStep): BoardColumn {
  return fromLuck('_dayun', '大运', step)
}

/** 一个流年 — 一列（`LiuNianStep` 与 `DaYunStep` 在这几个字段上同构）。 */
export function liunianColumn(step: LiuNianStep): BoardColumn {
  return fromLuck('_liunian', '流年', step)
}

function fromLuck(key: string, label: string,
                  s: DaYunStep | LiuNianStep): BoardColumn {
  // `ganzhi` 是保底：十神/藏干来自 `_luck_step` 的 `detail`，老记录可能没有。
  const gz = s.ganzhi ?? ''
  return {
    key, label,
    gan: s.gan ?? gz[0] ?? '', gan_wx: ganWx(s.gan ?? gz[0] ?? ''),
    zhi: s.zhi ?? gz[1] ?? '', zhi_wx: zhiWx(s.zhi ?? gz[1] ?? ''),
    shishen: s.gan_shishen ?? s.detail?.gan_shishen ?? '',
    cang_gan: s.detail?.cang_gan ?? [],
  }
}

/** 该字**未参与**本阶段（阶段 2 的流年，或被大运挡住的流年）——只有位置，没有内容。 */
export function emptyColumn(key: string, label: string): BoardColumn {
  return {
    key, label, gan: '', gan_wx: '', zhi: '', zhi_wx: '',
    shishen: '', cang_gan: [], dim: true,
  }
}

// 岁运两列的干支要**由字推五行**（这两个形状里没有现成的五行字段）——用全应用同一张表，
// 免得另立一份日后漂移。
const ganWx = (gan: string) => GAN_WUXING[gan] ?? ''
const zhiWx = (zhi: string) => ZHI_WUXING[zhi] ?? ''
