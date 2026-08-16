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

/** 已自动保存的排盘记录：结果页「编辑信息」PUT 更新对象。 */
export interface SavedRecordMeta {
  id: number
  person_name: string | null
  relationship: 'SELF' | 'CHILD' | 'PARENT' | 'OTHER'
  notes: string | null
}

/** Holds the latest computed chart + the inputs that produced it. */
export const useChartStore = defineStore('chart', {
  state: () => ({
    result: null as ChartResult | null,
    inputs: null as BirthInput | null,
    editDraft: null as EditDraft | null,
    savedRecord: null as SavedRecordMeta | null,
    /** 结果页当前选中大运干支（喜忌“大运介入”步联动） */
    viewingDayun: null as string | null,
  }),
  actions: {
    set(result: ChartResult, inputs: BirthInput) {
      this.result = result
      this.inputs = inputs
    },
    setSavedRecord(record: SavedRecordMeta | null) {
      this.savedRecord = record
    },
    setViewingDayun(ganzhi: string | null) {
      this.viewingDayun = ganzhi
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
      this.savedRecord = null
    },
  },
})
