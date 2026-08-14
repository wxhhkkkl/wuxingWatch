/** 五行 → 展示颜色（ChartDisplay / PillarTable / FortuneStrip 共用）。 */

export const WX_COLOR: Record<string, string> = {
  木: 'var(--wx-mu)',
  火: 'var(--wx-huo)',
  土: 'var(--wx-tu)',
  金: 'var(--wx-jin)',
  水: 'var(--wx-shui)',
}

export const GAN_WUXING: Record<string, string> = {
  甲: '木', 乙: '木', 丙: '火', 丁: '火', 戊: '土',
  己: '土', 庚: '金', 辛: '金', 壬: '水', 癸: '水',
}

export const ZHI_WUXING: Record<string, string> = {
  子: '水', 丑: '土', 寅: '木', 卯: '木', 辰: '土', 巳: '火',
  午: '火', 未: '土', 申: '金', 酉: '金', 戌: '土', 亥: '水',
}

export function wxColor(wx: string): string {
  return WX_COLOR[wx] ?? 'inherit'
}

/** 按天干/地支字符取五行色。 */
export function ganZhiColor(char: string): string {
  return wxColor(GAN_WUXING[char] ?? ZHI_WUXING[char] ?? '')
}
