import axios from 'axios'

function resolveDefaultApiBase() {
  if (typeof window === 'undefined') return 'http://127.0.0.1:8000'
  const { protocol, hostname } = window.location
  const isLocal = hostname === 'localhost' || hostname === '127.0.0.1'
  if (isLocal) return `${protocol}//${hostname}:8000`
  return `${protocol}//api-${hostname}`
}

const defaultApiBase = resolveDefaultApiBase()

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || defaultApiBase,
  timeout: 15000,
  withCredentials: true
})

function toError(error) {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) {
    return new Error(detail)
  }
  return new Error(error?.message || 'Request failed')
}

export function currentUserId() {
  return localStorage.getItem('auth_user_id') || ''
}

function setCurrentUserId(userId) {
  if (userId) localStorage.setItem('auth_user_id', userId)
}

function clearCurrentUserId() {
  localStorage.removeItem('auth_user_id')
}

export async function authSignUp(userId, password) {
  try {
    const { data } = await api.post('/auth/signup', {
      user_id: userId,
      password
    })
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function authLogin(userId, password) {
  try {
    const { data } = await api.post('/auth/login', {
      user_id: userId,
      password
    })
    setCurrentUserId(data.user_id)
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function authLogout() {
  try {
    const { data } = await api.post('/auth/logout')
    clearCurrentUserId()
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function authMe() {
  try {
    const { data } = await api.get('/auth/me')
    setCurrentUserId(data.user_id)
    return data
  } catch (error) {
    clearCurrentUserId()
    throw toError(error)
  }
}

export async function listProjects() {
  try {
    const { data } = await api.get('/projects')
    return data.projects
  } catch (error) {
    throw toError(error)
  }
}

export async function createProject(projectName) {
  try {
    const { data } = await api.post('/projects', {
      project_name: projectName
    })
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function getProject(projectId) {
  try {
    const { data } = await api.get(`/projects/${projectId}`)
    return data.project
  } catch (error) {
    throw toError(error)
  }
}

export async function updateProject(projectId, payload) {
  try {
    const { data } = await api.patch(`/projects/${projectId}`, payload)
    return data.project
  } catch (error) {
    throw toError(error)
  }
}

export async function copyProject(projectId, projectName) {
  try {
    const { data } = await api.post(`/projects/${projectId}/copy`, {
      project_name: projectName
    })
    return data.project
  } catch (error) {
    throw toError(error)
  }
}

export async function deleteProject(projectId) {
  try {
    const { data } = await api.delete(`/projects/${projectId}`)
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function listProjectFiles(projectId) {
  try {
    const { data } = await api.get(`/projects/${projectId}/files`)
    return data.files
  } catch (error) {
    throw toError(error)
  }
}

export async function uploadProjectFile(projectId, file) {
  try {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post(`/projects/${projectId}/files`, form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function deleteProjectFile(projectId, filename) {
  try {
    const { data } = await api.delete(`/projects/${projectId}/files/${encodeURIComponent(filename)}`)
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function runAnalysis(projectId, payload) {
  try {
    const { data } = await api.post(`/projects/${projectId}/analysis`, payload)
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function savePfo(projectId, equities, commissionConfig = null) {
  try {
    const payload = { equities }
    if (commissionConfig && typeof commissionConfig === 'object') {
      payload.commission_config = commissionConfig
    }
    const { data } = await api.put(`/projects/${projectId}/pfo`, payload)
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function getPfo(projectId) {
  try {
    const { data } = await api.get(`/projects/${projectId}/pfo`, {
      responseType: 'text'
    })
    return data
  } catch (error) {
    throw toError(error)
  }
}
