import axios from 'axios'
import { v4 as uuidv4 } from 'uuid'

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
  timeout: 15000
})

function toError(error) {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) {
    return new Error(detail)
  }
  return new Error(error?.message || 'Request failed')
}

export function ensureGuestId() {
  let id = localStorage.getItem('guest_uuid')
  if (!id) {
    id = uuidv4()
    localStorage.setItem('guest_uuid', id)
  }
  return id
}

export function guestId() {
  return ensureGuestId()
}

function withGuest(params = {}) {
  return { ...params, guest_id: guestId() }
}

export async function listProjects() {
  try {
    const { data } = await api.get('/projects', { params: withGuest() })
    return data.projects
  } catch (error) {
    throw toError(error)
  }
}

export async function createProject(projectName) {
  try {
    const { data } = await api.post('/projects', {
      guest_id: guestId(),
      project_name: projectName
    })
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function getProject(projectId) {
  try {
    const { data } = await api.get(`/projects/${projectId}`, { params: withGuest() })
    return data.project
  } catch (error) {
    throw toError(error)
  }
}

export async function updateProject(projectId, payload) {
  try {
    const { data } = await api.patch(`/projects/${projectId}`, {
      guest_id: guestId(),
      ...payload
    })
    return data.project
  } catch (error) {
    throw toError(error)
  }
}

export async function copyProject(projectId, projectName) {
  try {
    const { data } = await api.post(`/projects/${projectId}/copy`, {
      guest_id: guestId(),
      project_name: projectName
    })
    return data.project
  } catch (error) {
    throw toError(error)
  }
}

export async function deleteProject(projectId) {
  try {
    const { data } = await api.delete(`/projects/${projectId}`, { params: withGuest() })
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function listProjectFiles(projectId) {
  try {
    const { data } = await api.get(`/projects/${projectId}/files`, { params: withGuest() })
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
      params: withGuest(),
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function deleteProjectFile(projectId, filename) {
  try {
    const { data } = await api.delete(`/projects/${projectId}/files/${encodeURIComponent(filename)}`, {
      params: withGuest()
    })
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function runAnalysis(projectId, payload) {
  try {
    const { data } = await api.post(`/projects/${projectId}/analysis`, payload, {
      params: withGuest()
    })
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function savePfo(projectId, equities) {
  try {
    const { data } = await api.put(`/projects/${projectId}/pfo`, { equities }, {
      params: withGuest()
    })
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function getPfo(projectId) {
  try {
    const { data } = await api.get(`/projects/${projectId}/pfo`, {
      params: withGuest(),
      responseType: 'text'
    })
    return data
  } catch (error) {
    throw toError(error)
  }
}
