import { defineStore } from 'pinia'
import {
  createProject,
  deleteProject,
  deleteProjectFile,
  getProject,
  listProjectFiles,
  listProjects,
  updateProject,
  uploadProjectFile
} from '../api'

export const useProjectStore = defineStore('project', {
  state: () => ({
    projects: [],
    activeProject: null,
    files: [],
    loading: false,
    error: ''
  }),
  actions: {
    async loadProjects() {
      this.loading = true
      this.error = ''
      try {
        this.projects = await listProjects()
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    async create(name) {
      this.error = ''
      try {
        await createProject(name)
        await this.loadProjects()
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
    async deleteFile(projectId, filename) {
      this.error = ''
      try {
        await deleteProjectFile(projectId, filename)
        await this.loadFiles(projectId)
      } catch (e) {
        this.error = e.message
        throw e
      }
    }
  }
})
