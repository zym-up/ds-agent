import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useProjectStore = defineStore('project', () => {
  const currentId = ref(null)
  const currentName = ref('')
  const dataColumns = ref([])
  const dataShape = ref([0, 0])
  const steps = ref([])
  const chatHistory = ref([])

  function setProject(id, name, info) {
    currentId.value = id
    currentName.value = name
    if (info) {
      dataColumns.value = info.columns || []
      dataShape.value = info.shape || [0, 0]
    }
  }

  function setSteps(newSteps) {
    steps.value = newSteps
  }

  function addChatMessage(msg) {
    chatHistory.value.push(msg)
  }

  function clearProject() {
    currentId.value = null
    currentName.value = ''
    dataColumns.value = []
    dataShape.value = [0, 0]
    steps.value = []
    chatHistory.value = []
  }

  return { currentId, currentName, dataColumns, dataShape, steps, chatHistory,
           setProject, setSteps, addChatMessage, clearProject }
})
