import { defineStore } from 'pinia'
import type { BirthInput, ChartResult } from '../types'

/** "修改内容"草稿：回填表单 + 提交时更新原记录。 */
export interface EditDraft {
  recordId: number | null
  input: BirthInput
  meta?: {
    person_name?: string | null
    relationship?: 'SELF' | 'CHILD' | 'PARENT' | 'OTHER'
    notes?: string | null
  }
}

/** Holds the latest computed chart + the inputs that produced it. */
export const useChartStore = defineStore('chart', {
  state: () => ({
    result: null as ChartResult | null,
    inputs: null as BirthInput | null,
    editDraft: null as EditDraft | null,
  }),
  actions: {
    set(result: ChartResult, inputs: BirthInput) {
      this.result = result
      this.inputs = inputs
    },
    setEditDraft(draft: EditDraft) {
      this.editDraft = draft
    },
    clearEditDraft() {
      this.editDraft = null
    },
    clear() {
      this.result = null
      this.inputs = null
      this.editDraft = null
    },
  },
})
