import { config } from '@vue/test-utils'
import Vant from 'vant'

// Register Vant globally so components render in tests.
config.global.plugins = [Vant]
