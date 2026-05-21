import { useAuthStore } from '@/store/auth'

export function useAuth() {
  const { user, token, isAuthenticated, login, logout, setUser, setTokens } =
    useAuthStore()

  return {
    user,
    token,
    isAuthenticated,
    login,
    logout,
    setUser,
    setTokens,
  }
}
