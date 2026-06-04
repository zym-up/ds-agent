import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useProjectStore = defineStore('project', () => {
  const currentId = ref(null)
  const currentName = ref('')
  const dataFiles = ref([])
  const selectedDataFiles = ref([])
  const rounds = ref([])
  const currentRound = ref(-1)
  const chatHistory = ref([])
  const viewingStepIndex = ref(-1)
  const reportPreviewMode = ref(false)

  const steps = computed(() => {
    const cr = currentRound.value
    if (cr >= 0 && cr < rounds.value.length) {
      return rounds.value[cr].steps || []
    }
    return []
  })

  const doneSteps = computed(() =>
    steps.value.filter(s => s.status === 'done')
  )

  const allDoneSteps = computed(() => {
    const result = []
    for (const r of rounds.value) {
      for (const s of (r.steps || [])) {
        if (s.status === 'done') result.push(s)
      }
    }
    return result
  })

  const totalRows = computed(() =>
    dataFiles.value
      .filter(f => selectedDataFiles.value.includes(f.name))
      .reduce((sum, f) => sum + f.rows, 0)
  )

  function setProject(id, name, info) {
    currentId.value = id
    currentName.value = name
  }

  function setSteps(newSteps) {
    // Legacy: directly set steps on current round
    const cr = currentRound.value
    if (cr >= 0 && cr < rounds.value.length) {
      rounds.value[cr].steps = newSteps
    }
  }

  function addRound(userInput, explanation, newSteps) {
    rounds.value.push({
      user_input: userInput,
      plan_explanation: explanation,
      steps: newSteps || [],
      current_step: 0,
    })
    currentRound.value = rounds.value.length - 1
  }

  function setRounds(roundsData, cr) {
    rounds.value = roundsData || []
    currentRound.value = cr !== undefined ? cr : (roundsData.length ? roundsData.length - 1 : -1)
  }

  function setCurrentRound(index) {
    if (index >= 0 && index < rounds.value.length) {
      currentRound.value = index
      viewingStepIndex.value = -1
    }
  }

  function updateStep(index, updates) {
    const s = steps.value
    if (s[index]) {
      Object.assign(s[index], updates)
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
    rounds.value = []
    currentRound.value = -1
    chatHistory.value = []
    viewingStepIndex.value = -1
    reportPreviewMode.value = false
  }

  return {
    currentId, currentName, dataFiles, selectedDataFiles, steps, rounds, currentRound,
    chatHistory, viewingStepIndex, reportPreviewMode, totalRows, doneSteps, allDoneSteps,
    setProject, setSteps, setRounds, setCurrentRound, addRound,
    updateStep, addChatMessage, clearProject,
  }
})
