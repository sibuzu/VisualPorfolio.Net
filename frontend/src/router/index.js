import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ProjectView from '../views/ProjectView.vue'
import LoginView from '../views/LoginView.vue'
import AdminView from '../views/AdminView.vue'
import { authMe } from '../api'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView },
    { path: '/admin', component: AdminView },
    { path: '/', component: HomeView },
    { path: '/projects/:projectId', component: ProjectView }
  ]
})

router.beforeEach(async (to) => {
  if (to.path === '/login' || to.path === '/admin') return true
  try {
    await authMe()
    return true
  } catch {
    return '/login'
  }
})

export default router
