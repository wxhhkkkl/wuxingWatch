import { defineStore } from 'pinia'
import type { BirthInput, ChartResult } from '../types'

/** Holds the latest computed chart + the inputs that produced it. */
export const useChartStore = defineStore('chart', {
  state: () => ({
    result: null as ChartResult | null,
    inputs: null as BirthInput | null,
  }),
  actions: {
    set(result: ChartResult, inputs: BirthInput) {
      this.result = result
      this.inputs = inputs
    },
    clear() {
      this.result = null
      this.inputs = null
    },
  },
})
