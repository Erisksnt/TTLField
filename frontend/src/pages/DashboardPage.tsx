// frontend/src/pages/DashboardPage.tsx
import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Tooltip, Circle } from 'react-leaflet'
import { Icon } from 'leaflet'
import Layout from '@/components/Layout'
import api from '@/services/api'
import { Technician, Geofence } from '@/types'
import { Loader, MapPin, AlertCircle, RefreshCw } from 'lucide-react'
import { useWebSocket } from '@/hooks/useWebSocket'

interface PositionData {
  latitude: number
  longitude: number
  speed?: number
  battery_level?: number
}

// Ícone para técnicos online
const onlineIcon = new Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

// Ícone para técnicos offline
const offlineIcon = new Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-grey.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

// Função para buscar endereço
const fetchAddress = async (lat: number, lng: number): Promise<string> => {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`
    )
    const data = await response.json()
    return data.display_name || `${lat.toFixed(4)}, ${lng.toFixed(4)}`
  } catch (error) {
    console.error('Erro ao buscar endereço:', error)
    return `${lat.toFixed(4)}, ${lng.toFixed(4)}`
  }
}

// Função para formatar tempo decorrido
const timeAgo = (date: string | undefined | null): string => {
  if (!date) return 'N/A'
  const now = new Date()
  const past = new Date(date + 'Z') // força UTC
  const diffMs = now.getTime() - past.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffDay > 0) return `há ${diffDay} dia${diffDay > 1 ? 's' : ''}`
  if (diffHour > 0) return `há ${diffHour} hora${diffHour > 1 ? 's' : ''}`
  if (diffMin > 0) return `há ${diffMin} minuto${diffMin > 1 ? 's' : ''}`
  return `há ${diffSec} segundo${diffSec > 1 ? 's' : ''}`
}

export default function DashboardPage() {
  const [technicians, setTechnicians] = useState<Technician[]>([])
  const [geofences, setGeofences] = useState<Geofence[]>([])
  const [addresses, setAddresses] = useState<Record<string, string>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [mapError, setMapError] = useState(false)
  const [mapKey, setMapKey] = useState(0)
  const { lastPosition } = useWebSocket()

  const fetchTechnicians = async () => {
    try {
      const data = await api.getTechnicians(undefined, 0, 1000)
      setTechnicians(data)
      data.forEach(async (tech) => {
        if (tech.latitude && tech.longitude && !addresses[tech.id]) {
          const addr = await fetchAddress(tech.latitude, tech.longitude)
          setAddresses(prev => ({ ...prev, [tech.id]: addr }))
        }
      })
    } catch (error) {
      console.error('Erro ao carregar técnicos:', error)
    }
  }

  const fetchGeofences = async () => {
    try {
      const data = await api.getGeofences()
      setGeofences(data)
    } catch (error) {
      console.error('Erro ao carregar geofences:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchTechnicians()
    fetchGeofences()
  }, [])

  // Atualizar via WebSocket
  useEffect(() => {
    Object.entries(lastPosition).forEach(([techId, position]) => {
      const posData = position as PositionData
      setTechnicians(prev => prev.map(tech =>
        tech.id === techId
          ? { ...tech, latitude: posData.latitude, longitude: posData.longitude }
          : tech
      ))
      if (posData.latitude && posData.longitude && !addresses[techId]) {
        fetchAddress(posData.latitude, posData.longitude).then(addr => {
          setAddresses(prev => ({ ...prev, [techId]: addr }))
        })
      }
    })
  }, [lastPosition])

  const handleRetryMap = () => {
    setMapError(false)
    setMapKey(prev => prev + 1)
  }

  const handleRefresh = () => {
    fetchTechnicians()
    fetchGeofences()
  }

  const centerPosition: [number, number] = (() => {
    const withLocation = technicians.filter(t => t.latitude && t.longitude)
    if (withLocation.length > 0) {
      const avgLat = withLocation.reduce((sum, t) => sum + (t.latitude || 0), 0) / withLocation.length
      const avgLng = withLocation.reduce((sum, t) => sum + (t.longitude || 0), 0) / withLocation.length
      return [avgLat, avgLng]
    }
    return [-23.55, -46.63]
  })()

  const onlineTechnicians = technicians.filter(t => t.is_online)
  const offlineTechnicians = technicians.filter(t => !t.is_online)
  const lowBattery = technicians.filter(t => (t.battery_level || 100) < 20)

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          </div>
          <button
            onClick={handleRefresh}
            className="flex items-center gap-1 md:gap-2 bg-gray-500 hover:bg-gray-600 text-white font-semibold py-1.5 md:py-2 px-3 md:px-4 rounded-lg transition text-sm md:text-base">
            <RefreshCw size={14} className="md:w-4 md:h-4" />
            <span className="hidden sm:inline">Recarregar</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-gray-600 text-sm font-medium">Técnicos Online</h3>
            <p className="text-3xl font-bold text-blue-600 mt-2">{onlineTechnicians.length}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-gray-600 text-sm font-medium">Técnicos Offline</h3>
            <p className="text-3xl font-bold text-gray-600 mt-2">{offlineTechnicians.length}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-gray-600 text-sm font-medium">Total</h3>
            <p className="text-3xl font-bold text-gray-900 mt-2">{technicians.length}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-gray-600 text-sm font-medium">Bateria Baixa</h3>
            <p className="text-3xl font-bold text-yellow-600 mt-2">{lowBattery.length}</p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Mapa de Posições</h2>
          {isLoading ? (
            <div className="flex items-center justify-center h-96">
              <Loader className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : mapError ? (
            <div className="flex flex-col items-center justify-center h-96 bg-gray-100 rounded-lg">
              <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
              <p className="text-gray-700 font-medium mb-2">Erro ao carregar o mapa</p>
              <p className="text-gray-500 text-sm mb-4">Não foi possível conectar ao servidor de mapas</p>
              <button onClick={handleRetryMap} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition">
                <RefreshCw size={16} />
                Tentar novamente
              </button>
            </div>
          ) : (
            <div className="h-96 rounded-lg overflow-hidden">
              <MapContainer
                key={mapKey}
                center={centerPosition}
                zoom={12}
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  eventHandlers={{ error: () => setMapError(true) }}
                />

                {/* Geofences */}
                {geofences.map((geofence) => {
                  if (geofence.geofence_type === 'circle' && geofence.center_latitude && geofence.center_longitude) {
                    return (
                      <Circle
                        key={geofence.id}
                        center={[parseFloat(geofence.center_latitude), parseFloat(geofence.center_longitude)]}
                        radius={geofence.radius || 500}
                        pathOptions={{
                          color: geofence.is_active ? '#3b82f6' : '#999',
                          fillColor: geofence.is_active ? '#3b82f6' : '#999',
                          fillOpacity: 0.15,
                          weight: 1.5,
                        }}
                      >
                        <Tooltip sticky>
                          <div className="text-sm">
                            <p className="font-semibold">{geofence.name}</p>
                            <p className="text-gray-600">Raio: {geofence.radius || 500} m</p>
                            {geofence.address && (
                              <p className="text-gray-500 text-xs mt-1 truncate max-w-[200px]">📍 {geofence.address}</p>
                            )}
                          </div>
                        </Tooltip>
                      </Circle>
                    )
                  }
                  return null
                })}

                {/* Técnicos Online */}
                {onlineTechnicians
                  .filter((t) => t.latitude && t.longitude)
                  .map((technician) => (
                    <Marker
                      key={technician.id}
                      position={[technician.latitude!, technician.longitude!]}
                      icon={onlineIcon}
                    >
                      <Tooltip sticky>
                        <div className="text-sm">
                          <p className="font-semibold text-green-700">🟢 {technician.name}</p>
                          <p className="text-gray-600">{technician.employee_id}</p>
                          <p className="text-gray-600">Bateria: {technician.battery_level || 'N/A'}%</p>
                          <p className="text-xs text-gray-500 mt-1">
                            Última atualização: {technician.last_seen 
                              ? new Date(technician.last_seen + 'Z').toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' }) 
                              : 'N/A'}
                          </p>
                        </div>
                      </Tooltip>
                    </Marker>
                  ))}

                {/* Técnicos Offline */}
                {offlineTechnicians
                  .filter((t) => t.latitude && t.longitude)
                  .map((technician) => (
                    <Marker
                      key={technician.id}
                      position={[technician.latitude!, technician.longitude!]}
                      icon={offlineIcon}
                    >
                      <Tooltip sticky>
                        <div className="text-sm">
                          <p className="font-semibold text-gray-500">🔴 {technician.name}</p>
                          <p className="text-gray-600">{technician.employee_id}</p>
                          <p className="text-gray-600">Bateria: {technician.battery_level || 'N/A'}%</p>
                          <p className="text-xs text-gray-500 mt-1">
                            Última atualização: {technician.last_seen 
                              ? new Date(technician.last_seen + 'Z').toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' }) 
                              : 'N/A'}
                          </p>
                        </div>
                      </Tooltip>
                    </Marker>
                  ))}
              </MapContainer>
            </div>
          )}
        </div>

        {/* Técnicos Online */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <span className="w-3 h-3 bg-green-500 rounded-full inline-block"></span>
            Técnicos Online
          </h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {onlineTechnicians.length === 0 ? (
              <p className="text-gray-500 text-center py-8">Nenhum técnico online no momento</p>
            ) : (
              onlineTechnicians.map((technician) => (
                <div key={technician.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition">
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-900">{technician.name}</p>
                    <p className="text-sm text-gray-600">{technician.employee_id}</p>
                    {addresses[technician.id] && (
                      <p className="text-xs text-gray-500 mt-1 truncate max-w-[300px]" title={addresses[technician.id]}>
                        📍 {addresses[technician.id]}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-4 flex-shrink-0 ml-4">
                    <span className="text-sm text-gray-600">🔋 {technician.battery_level || 'N/A'}%</span>
                    <span className="text-xs text-gray-400">
                      {timeAgo(technician.last_seen)}
                    </span>
                    <span className="inline-block w-2 h-2 bg-green-500 rounded-full"></span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Técnicos Offline */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <span className="w-3 h-3 bg-gray-400 rounded-full inline-block"></span>
            Técnicos Offline
          </h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {offlineTechnicians.length === 0 ? (
              <p className="text-gray-500 text-center py-8">Nenhum técnico offline</p>
            ) : (
              offlineTechnicians.map((technician) => (
                <div key={technician.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition">
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-900">{technician.name}</p>
                    <p className="text-sm text-gray-600">{technician.employee_id}</p>
                    {addresses[technician.id] && (
                      <p className="text-xs text-gray-500 mt-1 truncate max-w-[300px]" title={addresses[technician.id]}>
                        📍 {addresses[technician.id]}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-4 flex-shrink-0 ml-4">
                    <span className="text-sm text-gray-600">🔋 {technician.battery_level || 'N/A'}%</span>
                    <span className="text-xs text-gray-400">
                      {timeAgo(technician.last_seen)}
                    </span>
                    <span className="inline-block w-2 h-2 bg-gray-400 rounded-full"></span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}