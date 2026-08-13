import { afterAll } from 'vitest'
import { config } from '@vue/test-utils'
import Vant from 'vant'

// Register Vant globally so components render in tests.
config.global.plugins = [Vant]

afterAll(() => new Promise((r) => setTimeout(r, 400)))
// van-nav-bar 等在 onMounted 后延迟 100/200/300ms 用 useRect 测占位高度。
// 等待这些定时器在 jsdom 环境销毁前触发，避免环境销毁后 `window is not defined` 的 flaky 未处理错误。
