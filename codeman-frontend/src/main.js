
import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import { authState, logout } from './store'

// Global Axios Request Interceptor
axios.interceptors.request.use(
  config => {
    // If token exists in store, attach it to headers
    if (authState.token) {
      config.headers.Authorization = `Bearer ${authState.token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// Global Axios Interceptor for 401
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      // Token expired
      if (authState.isAuthenticated) {
        // Only trigger if we thought we were logged in
        authState.showLoginModal = true // We need to add this to store
      }
    }
    return Promise.reject(error)
  }
)

// Force cache bust: 2026-02-25
console.log("App version: 2026-02-25.2")

const app = createApp(App)
app.use(router)
app.mount('#app')
