import { defineStore } from 'pinia'
import {
  createProject,
  createBuyHoldPerformance,
  copyProject,
  deleteProject,
  deleteProjectFile,
  getProject,
  listImportantProjects,
  listProjectFiles,
  listProjects,
  updateProject,
  uploadProjectFile
} from '../api'

export const useProjectStore = defineStore('project', {
  state: () => ({
    projects: [],
    importantProjects: [],
    activeProject: null,
    files: [],
    loading: false,
    error: ''
  }),
  actions: {
    _withTimeout(promise, ms, message) {
      let timer
      const timeout = new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error(message)), ms)
      })
      return Promise.race([promise, timeout]).finally(() => clearTimeout(timer))
    },
    async loadProjects() {
      this.loading = true
      this.error = ''
      try {
        const projects = await this._withTimeout(
          listProjects(),
          15000,
          '載入專案逾時，請檢查 API 網址與 Tunnel 設定'
        )
        this.projects = projects
        this.importantProjects = await this._withTimeout(
          listImportantProjects(),
          15000,
          '載入重要列表逾時，請檢查 API 網址與 Tunnel 設定'
        )
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    async create(name) {
      this.error = ''
      try {
        const created = await createProject(name)
        await this.loadProjects()
        return created?.project_id || created?.project?.project_id || ''
      } catch (e) {
        this.error = e.message
        throw e
      }
    },
    async remove(projectId) {
      this.error = ''
      try {
        await deleteProject(projectId)
        if (this.activeProject?.project_id === projectId) {
          this.activeProject = null
          this.files = []
        }
        await this.loadProjects()
      } catch (e) {
        this.error = e.message
        throw e
      }
    },
    async loadProject(projectId) {
      this.error = ''
      try {
        this.activeProject = await getProject(projectId)
        await this.loadFiles(projectId)
      } catch (e) {
        this.error = e.message
        this.activeProject = null
        this.files = []
        throw e
      }
    },
    async patchProject(projectId, payload) {
      this.error = ''
      try {
        this.activeProject = await updateProject(projectId, payload)
        await this.loadProjects()
      } catch (e) {
        this.error = e.message
        throw e
      }
    },
    async copy(projectId, projectName) {
      this.error = ''
      try {
        const project = await copyProject(projectId, projectName)
        await this.loadProjects()
        return project
      } catch (e) {
        this.error = e.message
        throw e
      }
    },
    async loadFiles(projectId) {
      this.error = ''
      try {
        this.files = await listProjectFiles(projectId)
      } catch (e) {
        this.error = e.message
        this.files = []
        throw e
      }
    },
    async uploadFile(projectId, file) {
      this.error = ''
      try {
        await uploadProjectFile(projectId, file)
        await this.loadFiles(projectId)
      } catch (e) {
        this.error = e.message
        throw e
      }
    },
    async uploadFiles(projectId, files) {
      this.error = ''
      try {
        for (const file of files) {
          await uploadProjectFile(projectId, file)
        }
        await this.loadFiles(projectId)
      } catch (e) {
        this.error = e.message
        throw e
      }
    },
    async deleteFile(projectId, filename) {
      this.error = ''
      try {
        await deleteProjectFile(projectId, filename)
        await this.loadFiles(projectId)
      } catch (e) {
        this.error = e.message
        throw e
      }
    },
    async createBuyHold(projectId, payload) {
      this.error = ''
      try {
        const result = await createBuyHoldPerformance(projectId, payload)
        await this.loadFiles(projectId)
        return result
      } catch (e) {
        this.error = e.message
        throw e
      }
    }
  }
})
