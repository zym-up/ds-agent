import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// Config
export const getConfig = () => api.get('/config')
export const saveConfig = (config) => api.post('/config', config)
export const testConnection = (config) => api.post('/config/test', config)

// Data (preview only, no project)
export const uploadData = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/data/upload', form)
}

// Projects
export const listProjects = () => api.get('/projects')
export const createProject = (name, file) => {
  const form = new FormData()
  form.append('name', name)
  form.append('file', file)
  return api.post('/projects', form)
}
export const getProject = (id) => api.get(`/projects/${id}`)
export const deleteProject = (id) => api.delete(`/projects/${id}`)
export const getProjectInfo = (id) => api.get(`/projects/${id}/info`)

// Data files
export const listDataFiles = (id) => api.get(`/projects/${id}/data`)
export const addDataFile = (id, file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/projects/${id}/data`, form)
}
export const mergeDataFiles = (id, selectedFiles) =>
  api.post(`/projects/${id}/data/merge`, { selected_files: selectedFiles })

// Analysis
export const planAnalysis = (projectId, userInput) =>
  api.post('/analysis/plan', { project_id: projectId, user_input: userInput })

export const executeStep = (projectId, stepIndex) =>
  api.post('/analysis/execute', { project_id: projectId, step_index: stepIndex })

// Reports
export const listReports = (id) => api.get(`/projects/${id}/reports`)
export const generateReport = (projectId, title, stepIndices, userNotes, includeConclusion) =>
  api.post('/report/generate', {
    project_id: projectId, title,
    step_indices: stepIndices || [],
    user_notes: userNotes || '',
    include_conclusion: includeConclusion !== false,
  })

// SSE helpers
export function streamPlan(projectId, userInput, onChunk, onDone) {
  return fetch('/api/analysis/plan/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId, user_input: userInput }),
  }).then(async (res) => {
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          if (data.done) { onDone(data.steps); return }
          if (data.chunk) onChunk(data.chunk)
        }
      }
    }
  })
}

export function streamExecute(projectId, stepIndex, onChunk, onResult, onDone) {
  return fetch('/api/analysis/execute/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId, step_index: stepIndex }),
  }).then(async (res) => {
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'result') onResult(data.text)
          if (data.type === 'explanation' && data.chunk) onChunk(data.chunk)
          if (data.type === 'done') { onDone(); return }
          if (data.type === 'error') { onDone(data.message); return }
        }
      }
    }
  })
}

export function streamConclude(projectId, stepIndices, userNotes, onChunk, onDone) {
  return fetch('/api/report/conclude/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId, step_indices: stepIndices, user_notes: userNotes }),
  }).then(async (res) => {
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          if (data.done) { onDone(); return }
          if (data.chunk) onChunk(data.chunk)
          if (data.error) { onDone(data.error); return }
        }
      }
    }
  })
}
