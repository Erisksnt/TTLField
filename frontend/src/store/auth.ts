// frontend/src/store/auth.ts
import { create } from 'zustand'
import { AuthState, User } from '@/types'
import api from '@/services/api'

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  isLoading: false,
  isAuthenticated: !!localStorage.getItem('access_token'),

  login: async (email: string, password: string) => {
    set({ isLoading: true })
    try {
      const response = await api.login(email, password)

      if (response.access_token) {
        localStorage.setItem('access_token', response.access_token)
        localStorage.setItem('refresh_token', response.refresh_token)
      }

      const user = await api.getCurrentUser()

      set({
        user: user, 
        token: response.access_token,
        refreshToken: response.refresh_token,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error) {
      console.error('❌ Erro no login:', error)
      set({ isLoading: false })
      throw error
    }
  },

  logout: () => {
    api.logout().catch(() => {})
    
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
    })
  },

  setUser: (user: User) => {
    set({ user })
  },

  setTokens: (access: string, refresh: string) => {
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
    set({
      token: access,
      refreshToken: refresh,
      isAuthenticated: true,
    })
  },

  checkAuth: async () => {
    const token = get().token
    if (!token) {
      return false
    }
    try {
      const user = await api.getCurrentUser()
      set({ user, isAuthenticated: true })
      return true
    } catch (error) {
      console.error('❌ Erro no checkAuth:', error)
      get().logout()
      return false
    }
  },
}))