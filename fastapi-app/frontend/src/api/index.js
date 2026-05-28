import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const uploadData = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/data/upload', form)
}

export const getConfig = () => api.get('/config')
export const saveConfig = (config) => api.post('/config', config)
export const testConnection = (config) => api.post('/config/test', config)

export const listProjects = () => api.get('/projects')
export const createProject = (name, file) => {
  const form = new FormData()
  form.append('name', name)
  if (file) form.append('file', file)
  return api.post('/projects', form)
}
export const getProject = (id) => api.get(`/projects/${id}`)
export const deleteProject = (id) => api.delete(`/projects/${id}`)

export const planAnalysis = (projectId, userInput) =>
  api.post('/analysis/plan', { project_id: projectId, user_input: userInput })

export const executeStep = (projectId, stepIndex) =>
  api.post('/analysis/execute', { project_id: projectId, step_index: stepIndex })

export const generateReport = (projectId, title, conclusion) =>
  api.post('/report/generate', { project_id: projectId, title, conclusion })
