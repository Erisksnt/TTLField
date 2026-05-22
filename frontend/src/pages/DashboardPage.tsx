// frontend/src/pages/DashboardPage.tsx
import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import { Icon } from 'leaflet'
import Layout from '@/components/Layout'
import api from '@/services/api'
import { Technician } from '@/types'
import { Loader, MapPin, AlertCircle, RefreshCw } from 'lucide-react'

const customIcon = new Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

export default function DashboardPage() {
  const [technicians, setTechnicians] = useState<Technician[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [mapError, setMapError] = useState(false)
  const [mapKey, setMapKey] = useState(0) // Para forçar recarga do mapa

  const fetchTechnicians = async () => {
    try {
      const data = await api.getTechnicians(true) // Apenas online
      setTechnicians(data)
    } catch (error) {
      console.error('Erro ao carregar técnicos:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchTechnicians()
    const interval = setInterval(fetchTechnicians, 10000) // Atualizar a cada 10s

    return () => clearInterval(interval)
  }, [])

  const handleRetryMap = () => {
    setMapError(false)
    setMapKey(prev => prev + 1) // Recarregar o mapa
  }

  // Calcular posição central baseada nos técnicos ou fallback
  const centerPosition = (() => {
    const onlineWithLocation = technicians.filter(t => t.latitude && t.longitude && t.is_online)
    if (onlineWithLocation.length > 0) {
      const avgLat = onlineWithLocation.reduce((sum, t) => sum + (t.latitude || 0), 0) / onlineWithLocation.length
      const avgLng = onlineWithLocation.reduce((sum, t) => sum + (t.longitude || 0), 0) / onlineWithLocation.length
      return [avgLat, avgLng] as [number, number]
    }
    return [-23.55, -46.63] // São Paulo como fallback
  })()

  const onlineTechnicians = technicians.filter(t => t.is_online)
  const lowBattery = technicians.filter(t => (t.battery_level || 100) < 20)

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600">Monitoramento em tempo real</p>
          </div>
          <button
            onClick={() => fetchTechnicians()}
            className="flex items-center gap-2 bg-gray-500 hover:bg-gray-600 text-white font-semibold py-2 px-4 rounded-lg transition"
            title="Recarregar"
          >
            <RefreshCw size={20} />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-gray-600 text-sm font-medium">Técnicos Online</h3>
            <p className="text-3xl font-bold text-blue-600 mt-2">{onlineTechnicians.length}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-gray-600 text-sm font-medium">Técnicos Total</h3>
            <p className="text-3xl font-bold text-gray-700 mt-2">{technicians.length}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-gray-600 text-sm font-medium">Bateria Baixa</h3>
            <p className="text-3xl font-bold text-yellow-600 mt-2">{lowBattery.length}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-gray-600 text-sm font-medium">Alertas Ativos</h3>
            <p className="text-3xl font-bold text-red-600 mt-2">0</p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Mapa em Tempo Real</h2>
          {isLoading ? (
            <div className="flex items-center justify-center h-96">
              <Loader className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : mapError ? (
            <div className="flex flex-col items-center justify-center h-96 bg-gray-100 rounded-lg">
              <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
              <p className="text-gray-700 font-medium mb-2">Erro ao carregar o mapa</p>
              <p className="text-gray-500 text-sm mb-4">Não foi possível conectar ao servidor de mapas</p>
              <button
                onClick={handleRetryMap}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition"
              >
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
                  eventHandlers={{
                    error: () => setMapError(true),
                  }}
                />
                {onlineTechnicians
                  .filter((t) => t.latitude && t.longitude)
                  .map((technician) => (
                    <Marker
                      key={technician.id}
                      position={[technician.latitude!, technician.longitude!]}
                      icon={customIcon}
                    >
                      <Popup>
                        <div className="text-sm">
                          <p className="font-semibold">{technician.name}</p>
                          <p className="text-gray-600">{technician.employee_id}</p>
                          <p className="text-gray-600">Bateria: {technician.battery_level || 'N/A'}%</p>
                          <p className="text-xs text-gray-500 mt-1">
                            Última atualização: {technician.last_seen ? new Date(technician.last_seen).toLocaleTimeString() : 'N/A'}
                          </p>
                        </div>
                      </Popup>
                    </Marker>
                  ))}
              </MapContainer>
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <MapPin className="w-5 h-5 text-green-600" />
            Técnicos Online
          </h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {onlineTechnicians.length === 0 ? (
              <p className="text-gray-500 text-center py-8">Nenhum técnico online no momento</p>
            ) : (
              onlineTechnicians.map((technician) => (
                <div key={technician.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition">
                  <div>
                    <p className="font-semibold text-gray-900">{technician.name}</p>
                    <p className="text-sm text-gray-600">{technician.employee_id}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-600">
                      🔋 {technician.battery_level || 'N/A'}%
                    </span>
                    <span className="inline-block w-2 h-2 bg-green-500 rounded-full"></span>
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