export interface User {
  id: string
  email: string
  username: string
  full_name?: string
  role: 'user' | 'manager' | 'admin' | 'supervisor'
  is_active: boolean
  created_at: string
  updated_at: string
  last_login?: string
}

export interface Technician {
  id: string
  name: string
  employee_id: string
  email?: string
  phone?: string
  is_active: boolean
  is_online: boolean
  latitude?: number
  longitude?: number
  accuracy?: number
  battery_level?: number
  device_id?: string
  last_seen?: string
  created_at: string
  updated_at: string
}

export interface Position {
  id: string
  technician_id: string
  device_id: string
  latitude: number
  longitude: number
  accuracy?: number
  altitude?: number
  speed?: number
  heading?: number
  battery_level?: number
  battery_status?: string
  provider: string
  is_valid: boolean
  timestamp: string
  received_at: string
}

export interface Geofence {
  id: string
  name: string
  description?: string
  geofence_type: 'circle' | 'polygon' | 'rectangle'
  geometry: Record<string, unknown>
  is_active: boolean
  alert_on_enter: boolean
  alert_on_exit: boolean
  created_at: string
  updated_at: string
}

export interface Alert {
  id: string
  technician_id: string
  device_id: string
  geofence_id?: string
  alert_type: string
  title: string
  description?: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  is_active: boolean
  is_acknowledged: boolean
  acknowledged_at?: string
  acknowledged_by?: string
  triggered_at: string
  resolved_at?: string
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setUser: (user: User) => void
  setTokens: (access: string, refresh: string) => void
}

export interface MapLocation {
  id: string
  name: string
  latitude: number
  longitude: number
  is_online: boolean
  battery_level?: number
  last_seen?: string
}

export interface RouteData {
  technician_id: string
  distance_km: number
  start_datetime: string
  end_datetime: string
}