import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Forum from '../views/Forum.vue'
import Showcase from '../views/Showcase.vue'
import PostDetail from '../views/PostDetail.vue'
import UserProfile from '../views/UserProfile.vue'
import SearchResults from '../views/SearchResults.vue'
import WorkDetail from '../views/WorkDetail.vue'
import AdminBanner from '../views/AdminBanner.vue'
import BcmPostDetail from '../views/BcmPostDetail.vue'
import About from '../views/About.vue'
import Authorize from '../views/Authorize.vue'
import Developer from '../views/Developer.vue'
import DeveloperDocs from '../views/DeveloperDocs.vue'
import DeveloperDashboard from '../views/DeveloperDashboard.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import { authState } from '../store.js'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/admin',
      component: AdminDashboard,
      meta: { requiresAdmin: true }
    },
    {
      path: '/developer',
      component: Developer,
      children: [
        { path: '', redirect: '/developer/docs' },
        { path: 'docs', component: DeveloperDocs },
        { path: 'dashboard', component: DeveloperDashboard }
      ]
    },
    {
      path: '/oauth/authorize',
      name: 'oauth-authorize',
      component: Authorize
    },
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/about',
      name: 'about',
      component: About
    },
    {
      path: '/forum/bcm/:id',
      name: 'bcm-post-detail',
      component: BcmPostDetail
    },
    {
      path: '/admin/banners',
      name: 'admin-banners',
      component: AdminBanner
    },
    {
      path: '/work/:id',
      name: 'work-detail',
      component: WorkDetail
    },
    {
      path: '/search',
      name: 'search-results',
      component: SearchResults
    },
    {
      path: '/login',
      name: 'login',
      component: Login
    },
    {
      path: '/forum',
      name: 'forum',
      component: Forum
    },
    {
      path: '/forum/:id',
      name: 'post-detail',
      component: PostDetail
    },
    {
      path: '/showcase',
      name: 'showcase',
      component: Showcase
    },
    {
      path: '/user/:id',
      name: 'user-profile',
      component: UserProfile
    }
  ]
})

// Global Navigation Guard
router.beforeEach((to, from, next) => {
  // Check if user is authenticated
  const isAuthenticated = authState.isAuthenticated
  
  // If not authenticated and trying to access any page other than login
  if (!isAuthenticated && to.name !== 'login') {
    // Redirect to login
    next({ name: 'login' })
  } else {
    // Proceed
    if (to.meta.requiresAdmin && !authState.isAdmin) {
      next('/')
    } else {
      next()
    }
  }
})

export default router
