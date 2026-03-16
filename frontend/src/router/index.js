import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ProjectView from '../views/ProjectView.vue'
import LoginView from '../views/LoginView.vue'
import AdminView from '../views/AdminView.vue'
import { authGuest, authMe } from '../api'

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
    const me = await authMe()
    if (me?.user_id === 'guest' && !to.path.startsWith('/projects/')) {
      return '/login'
    }
    return true
  } catch {
    if (to.path.startsWith('/projects/')) {
      try {
        await authGuest()
        return true
      } catch {
        // Fall through to regular login page.
      }
    }
    return {
      path: '/login',
      query: { redirect: to.fullPath }
    }
  }
})

export default router
