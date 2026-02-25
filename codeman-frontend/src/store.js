import { reactive, computed } from 'vue'

export const authState = reactive({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  showLoginModal: false, // For re-login dialog
  isAdmin: computed(() => authState.user?.is_admin || false)
})

export function login(data) {
  localStorage.setItem('token', data.token)
  localStorage.setItem('user', JSON.stringify(data.user))
  localStorage.setItem('userId', data.user.id)
  
  authState.user = data.user
  authState.token = data.token
  authState.isAuthenticated = true
}

export function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  localStorage.removeItem('userId')
  
  authState.user = null
  authState.token = null
  authState.isAuthenticated = false
}
