import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useProjectStore = defineStore('project', () => {
  const currentId = ref(null)
  const currentName = ref('')
  const dataFiles = ref([])
  const selectedDataFiles = ref([])
  const steps = ref([])
  const chatHistory = ref([])
  const viewingStepIndex = ref(-1)
  const reportPreviewMode = ref(false)

  const totalRows = computed(() =>
    dataFiles.value
      .filter(f => selectedDataFiles.value.includes(f.name))
      .reduce((sum, f) => sum + f.rows, 0)
  )

  const doneSteps = computed(() =>
    steps.value.filter(s => s.status === 'done')
  )

  function setProject(id, name, info) {
    currentId.value = id
    currentName.value = name
  }

  function setSteps(newSteps) {
    steps.value = newSteps
  }

  function updateStep(index, updates) {
    if (steps.value[index]) {
      Object.assign(steps.value[index], updates)
    }
  }

  function addChatMessage(msg) {
    chatHistory.value.push(msg)
  }

  function clearProject() {
    currentId.value = null
    currentName.value = ''
    dataFiles.value = []
    selectedDataFiles.value = []
    steps.value = []
    chatHistory.value = []
    viewingStepIndex.value = -1
    reportPreviewMode.value = false
  }

  return {
    currentId, currentName, dataFiles, selectedDataFiles, steps, chatHistory,
    viewingStepIndex, reportPreviewMode, totalRows, doneSteps,
    setProject, setSteps, updateStep, addChatMessage, clearProject,
  }
})
