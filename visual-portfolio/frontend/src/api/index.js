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

export async function authGuest() {
  try {
    const { data } = await api.post('/auth/guest')
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

export async function adminLogin(password) {
  try {
    const { data } = await api.post('/auth/admin/login', { password })
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function adminMe() {
  try {
    const { data } = await api.get('/auth/admin/me')
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function adminLogout() {
  try {
    const { data } = await api.post('/auth/admin/logout')
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function adminListProjects() {
  try {
    const { data } = await api.get('/admin/projects')
    return data.projects || []
  } catch (error) {
    throw toError(error)
  }
}

export async function adminDeleteProject(projectId) {
  try {
    const { data } = await api.delete(`/admin/projects/${projectId}`)
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function adminSetDemoProject(projectId) {
  try {
    const { data } = await api.post(`/admin/projects/${projectId}/set-demo`)
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function adminListUsers() {
  try {
    const { data } = await api.get('/admin/users')
    return data.users || []
  } catch (error) {
    throw toError(error)
  }
}

export async function adminDeleteUser(userId) {
  try {
    const { data } = await api.delete(`/admin/users/${encodeURIComponent(userId)}`)
    return data
  } catch (error) {
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

export async function listImportantProjects() {
  try {
    const { data } = await api.get('/projects/important')
    return data.projects || []
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

export async function downloadProjectPackage(projectId) {
  try {
    const response = await api.get(`/projects/${projectId}/download`, {
      responseType: 'blob'
    })
    const disposition = String(response.headers?.['content-disposition'] || '')
    const m = disposition.match(/filename="?([^"]+)"?/i)
    return {
      blob: response.data,
      filename: (m?.[1] || `${projectId}.gsea`).trim()
    }
  } catch (error) {
    throw toError(error)
  }
}

export async function downloadDynamicCompoundingReport(projectId, mode, payload) {
  try {
    const response = await api.post(
      `/projects/${projectId}/analysis/dynamic-compounding/${encodeURIComponent(mode)}/download`,
      payload,
      { responseType: 'blob', timeout: 120000 }
    )
    const disposition = String(response.headers?.['content-disposition'] || '')
    const encodedMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i)
    const plainMatch = disposition.match(/filename="?([^";]+)"?/i)
    let filename = `${projectId}-${mode}.sea`
    if (encodedMatch?.[1]) {
      filename = decodeURIComponent(encodedMatch[1].trim())
    } else if (plainMatch?.[1]) {
      filename = plainMatch[1].trim()
    }
    return { blob: response.data, filename }
  } catch (error) {
    throw toError(error)
  }
}

export async function uploadProjectPackage(projectId, projectName, file) {
  try {
    const form = new FormData()
    form.append('project_name', projectName)
    form.append('file', file)
    const { data } = await api.post(`/projects/${projectId}/upload`, form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return data
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

export async function createBuyHoldPerformance(projectId, payload) {
  try {
    const { data } = await api.post(`/projects/${projectId}/buy-hold`, payload)
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function listProjectAttachments(projectId) {
  try {
    const { data } = await api.get(`/projects/${projectId}/files/attachments`)
    return data.attachments || []
  } catch (error) {
    throw toError(error)
  }
}

export async function uploadProjectAttachment(projectId, file) {
  try {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post(`/projects/${projectId}/files/attachments`, form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function deleteProjectAttachment(projectId, filename) {
  try {
    const { data } = await api.delete(`/projects/${projectId}/files/attachments/${encodeURIComponent(filename)}`)
    return data
  } catch (error) {
    throw toError(error)
  }
}

export function getProjectAttachmentUrl(projectId, filename) {
  return `${api.defaults.baseURL}/projects/${projectId}/files/attachments/${encodeURIComponent(filename)}`
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function shouldRetryAnalysis(error) {
  const code = String(error?.code || '')
  const msg = String(error?.message || '').toLowerCase()
  if (code === 'ECONNABORTED') return true
  if (code === 'ERR_NETWORK') return true
  if (msg.includes('timeout')) return true
  if (!error?.response) return true
  return false
}

export async function runAnalysis(projectId, payload) {
  const createUrl = `/projects/${projectId}/analysis/jobs`
  const maxAttempts = 2
  const pollIntervalMs = 1200
  const pollMaxMs = 8 * 60 * 1000

  let lastError = null
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const createResp = await api.post(createUrl, payload)
      const jobId = createResp?.data?.job_id
      if (!jobId) {
        throw new Error('Analysis job_id missing')
      }

      const start = Date.now()
      while (Date.now() - start < pollMaxMs) {
        const { data: statusData } = await api.get(`/projects/${projectId}/analysis/jobs/${encodeURIComponent(jobId)}`)
        const status = String(statusData?.status || '')
        if (status === 'done') {
          const { data } = await api.get(`/projects/${projectId}/analysis/jobs/${encodeURIComponent(jobId)}/result`)
          return data
        }
        if (status === 'failed') {
          throw new Error(statusData?.error || 'Analysis job failed')
        }
        await sleep(pollIntervalMs)
      }

      throw new Error('Analysis polling timeout')
    } catch (error) {
      lastError = error
      if (attempt >= maxAttempts || !shouldRetryAnalysis(error)) {
        throw toError(error)
      }
      await sleep(1000)
    }
  }
  throw toError(lastError)
}

export async function saveGseaGroup(
  projectId,
  equities,
  commissionConfig = null,
  description = '',
  dateRangeConfig = null,
  sharpeConfig = null,
  dynamicCompoundingConfig = null
) {
  try {
    const payload = { equities }
    if (commissionConfig && typeof commissionConfig === 'object') {
      payload.commission_config = commissionConfig
    }
    payload.description = String(description || '')
    if (dateRangeConfig && typeof dateRangeConfig === 'object') {
      payload.date_range_config = {
        enabled: !!dateRangeConfig.enabled,
        start: String(dateRangeConfig.start || ''),
        end: String(dateRangeConfig.end || '')
      }
    }
    if (sharpeConfig && typeof sharpeConfig === 'object') {
      payload.sharpe_config = {
        capital: Number(sharpeConfig.capital || 0),
        risk_free_rate: Number(sharpeConfig.risk_free_rate || 0)
      }
    }
    if (dynamicCompoundingConfig && typeof dynamicCompoundingConfig === 'object') {
      payload.dynamic_compounding_config = {
        initial_capital: Number(dynamicCompoundingConfig.initial_capital || 0),
        initial_ratio: Number(dynamicCompoundingConfig.initial_ratio || 0),
        add_threshold_profit: Number(dynamicCompoundingConfig.add_threshold_profit || 0),
        add_ratio: Number(dynamicCompoundingConfig.add_ratio || 0),
        rollback_amount: Number(dynamicCompoundingConfig.rollback_amount || 0),
        rollback_percent: Number(dynamicCompoundingConfig.rollback_percent || 0),
        max_multiple: Number(dynamicCompoundingConfig.max_multiple || 0)
      }
    }
    const { data } = await api.put(`/projects/${projectId}/gsea-group`, payload)
    return data
  } catch (error) {
    throw toError(error)
  }
}

export async function getGseaGroup(projectId) {
  try {
    const { data } = await api.get(`/projects/${projectId}/gsea-group`, {
      responseType: 'text'
    })
    return data
  } catch (error) {
    throw toError(error)
  }
}
