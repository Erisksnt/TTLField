import axios, { AxiosInstance } from 'axios'
import { TokenResponse, User, Technician, Position, Geofence, Alert } from '@/types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiService {
  private api: AxiosInstance

  constructor() {
    this.api = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Interceptor para adicionar token
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Interceptor para erros
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  // Auth
  async login(email: string, password: string): Promise<TokenResponse> {
    const response = await this.api.post<TokenResponse>('/auth/login', {
      email,
      password,
    })
    return response.data
  }

  async register(data: {
    email: string
    username: string
    password: string
    full_name?: string
  }): Promise<{ message: string; user_id: string }> {
    const response = await this.api.post('/auth/register', data)
    return response.data
  }

  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    const response = await this.api.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  }

  // Technicians
  async getTechnicians(
    isOnline?: boolean,
    skip: number = 0,
    limit: number = 100
  ): Promise<Technician[]> {
    const response = await this.api.get<Technician[]>('/technicians', {
      params: { is_online: isOnline, skip, limit },
    })
    return response.data
  }

  async getTechnicianById(id: string): Promise<Technician> {
    const response = await this.api.get<Technician>(`/technicians/${id}`)
    return response.data
  }

  async createTechnician(data: Partial<Technician>): Promise<Technician> {
    const response = await this.api.post<Technician>('/technicians', data)
    return response.data
  }

  async updateTechnician(
    id: string,
    data: Partial<Technician>
  ): Promise<Technician> {
    const response = await this.api.patch<Technician>(`/technicians/${id}`, data)
    return response.data
  }

  async deleteTechnician(id: string): Promise<void> {
    await this.api.delete(`/technicians/${id}`)
  }

  // Positions
  async createPosition(
    technicianId: string,
    deviceId: string,
    position: Partial<Position>
  ): Promise<Position> {
    const response = await this.api.post<Position>('/positions', position, {
      params: { technician_id: technicianId, device_id: deviceId },
    })
    return response.data
  }

  async getTechnicianPositions(
    technicianId: string,
    hours: number = 24,
    limit: number = 1000
  ): Promise<Position[]> {
    const response = await this.api.get<Position[]>(
      `/positions/${technicianId}`,
      {
        params: { hours, limit },
      }
    )
    return response.data
  }

  async getAllCurrentPositions(): Promise<Position[]> {
    const response = await this.api.get<Position[]>('/positions/current/all')
    return response.data
  }

  async calculateDistance(
    technicianId: string,
    startTime: string,
    endTime: string
  ): Promise<{ distance_km: number }> {
    const response = await this.api.get(`/positions/${technicianId}/distance`, {
      params: { start_datetime: startTime, end_datetime: endTime },
    })
    return response.data
  }

  // Geofences
  async getGeofences(): Promise<Geofence[]> {
    const response = await this.api.get<Geofence[]>('/geofences')
    return response.data
  }

  async createGeofence(data: Partial<Geofence>): Promise<Geofence> {
    const response = await this.api.post<Geofence>('/geofences', data)
    return response.data
  }

  async updateGeofence(
    id: string,
    data: Partial<Geofence>
  ): Promise<Geofence> {
    const response = await this.api.patch<Geofence>(`/geofences/${id}`, data)
    return response.data
  }

  async deleteGeofence(id: string): Promise<void> {
    await this.api.delete(`/geofences/${id}`)
  }

  // Alerts
  async getAlerts(params?: Record<string, unknown>): Promise<Alert[]> {
    const response = await this.api.get<Alert[]>('/alerts', { params })
    return response.data
  }

  async acknowledgeAlert(id: string, acknowledgedBy: string): Promise<Alert> {
    const response = await this.api.post<Alert>(
      `/alerts/${id}/acknowledge`,
      { acknowledged_by: acknowledgedBy }
    )
    return response.data
  }

  // Health
  async healthCheck(): Promise<{ status: string }> {
    const response = await this.api.get('/health')
    return response.data
  }
}

export default new ApiService()
