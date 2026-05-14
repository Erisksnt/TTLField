import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import { Icon } from 'leaflet'
import Layout from '@/components/Layout'
import api from '@/services/api'
import { Position, Technician } from '@/types'
import { Loader } from 'lucide-react'

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

  useEffect(() => {
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

    fetchTechnicians()
    const interval = setInterval(fetchTechnicians, 10000) // Atualizar a cada 10s

    return () => clearInterval(interval)
  }, [])

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600">Monitoramento em tempo real</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-gray-600 text-sm font-medium">Técnicos Online</h3>
            <p className="text-3xl font-bold text-blue-600 mt-2">
              {technicians.filter((t) => t.is_online).length}
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-gray-600 text-sm font-medium">Técnicos Total</h3>
            <p className="text-3xl font-bold text-gray-700 mt-2">{technicians.length}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-gray-600 text-sm font-medium">Bateria Baixa</h3>
            <p className="text-3xl font-bold text-yellow-600 mt-2">
              {technicians.filter((t) => (t.battery_level || 100) < 20).length}
            </p>
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
          ) : (
            <div className="h-96 rounded-lg overflow-hidden">
              <MapContainer center={[-23.55, -46.63]} zoom={11} style={{ height: '100%' }}>
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; OpenStreetMap contributors'
                />
                {technicians
                  .filter((t) => t.latitude && t.longitude && t.is_online)
                  .map((technician) => (
                    <Marker
                      key={technician.id}
                      position={[technician.latitude || 0, technician.longitude || 0]}
                      icon={customIcon}
                    >
                      <Popup>
                        <div className="text-sm">
                          <p className="font-semibold">{technician.name}</p>
                          <p className="text-gray-600">{technician.employee_id}</p>
                          <p className="text-gray-600">
                            Bateria: {technician.battery_level || 'N/A'}%
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
          <h2 className="text-xl font-bold mb-4">Técnicos Online</h2>
          <div className="space-y-2">
            {technicians
              .filter((t) => t.is_online)
              .map((technician) => (
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
              ))}
          </div>
        </div>
      </div>
    </Layout>
  )
}