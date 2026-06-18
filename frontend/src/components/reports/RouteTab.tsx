// frontend/src/components/reports/RouteTab.tsx
import { MapContainer, TileLayer, Polyline, Marker, Tooltip } from 'react-leaflet'
import { Icon } from 'leaflet'
import { useState, useEffect } from 'react'

// Ícone para pontos da rota
const routeIcon = new Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

// Ícone para início (verde) e fim (vermelho)
const startIcon = new Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

const endIcon = new Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

interface RoutePoint {
  latitude: number
  longitude: number
  timestamp: string
  speed?: number
}

interface RouteTabProps {
  data?: RoutePoint[]
}

// Função haversine para calcular distância entre dois pontos (em km)
const haversineDistance = (lat1: number, lon1: number, lat2: number, lon2: number): number => {
  const R = 6371 // raio da Terra em km
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
  return R * c
}

// Formatar tempo em horas e minutos
const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${Math.round(seconds)}s`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}min`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins === 0 ? `${hours}h` : `${hours}h ${mins}min`
}

export default function RouteTab({ data }: RouteTabProps) {
  if (!data || data.length < 2) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p className="text-lg">🗺️ Nenhuma rota encontrada para o período selecionado</p>
        <p className="text-sm mt-1">Selecione um técnico e um período com pelo menos duas posições registradas.</p>
      </div>
    )
  }

  // Converter pontos para formato [lat, lng]
  const positions: [number, number][] = data.map(p => [p.latitude, p.longitude])
  const startPoint = positions[0]
  const endPoint = positions[positions.length - 1]

  // Calcular centro do mapa
  const centerLat = data.reduce((sum, p) => sum + p.latitude, 0) / data.length
  const centerLng = data.reduce((sum, p) => sum + p.longitude, 0) / data.length

  // Calcular métricas
  let totalDistance = 0
  let totalTime = 0
  let maxSpeed = 0
  let avgSpeed = 0

  for (let i = 1; i < data.length; i++) {
    const prev = data[i-1]
    const curr = data[i]
    const dist = haversineDistance(prev.latitude, prev.longitude, curr.latitude, curr.longitude)
    totalDistance += dist

    // Tempo entre pontos (em segundos)
    const tPrev = new Date(prev.timestamp).getTime()
    const tCurr = new Date(curr.timestamp).getTime()
    const timeDiff = (tCurr - tPrev) / 1000 // segundos
    totalTime += timeDiff

    // Velocidade (km/h)
    if (timeDiff > 0) {
      const speed = (dist / timeDiff) * 3600 // km/h
      if (speed > maxSpeed) maxSpeed = speed
    }
  }

  avgSpeed = totalTime > 0 ? (totalDistance / totalTime) * 3600 : 0

  return (
    <div>
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
        <p className="text-sm text-blue-700">
          <strong>🗺️ Rota percorrida</strong> – {data.length} pontos registrados.
          Distância total: <strong>{totalDistance.toFixed(2)} km</strong>
        </p>
      </div>

      <div className="h-96 rounded-lg overflow-hidden border">
        <MapContainer
          center={[centerLat, centerLng]}
          zoom={14}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; OpenStreetMap contributors'
          />

          {/* Linha da rota */}
          <Polyline
            positions={positions}
            color="#3b82f6"
            weight={4}
            opacity={0.8}
          />

          {/* Ponto de início */}
          <Marker position={startPoint} icon={startIcon}>
            <Tooltip sticky>
              <div className="text-sm">
                <p className="font-semibold text-green-700">Início</p>
                <p className="text-gray-600">{new Date(data[0].timestamp).toLocaleString('pt-BR')}</p>
              </div>
            </Tooltip>
          </Marker>

          {/* Ponto de fim */}
          <Marker position={endPoint} icon={endIcon}>
            <Tooltip sticky>
              <div className="text-sm">
                <p className="font-semibold text-red-700">Fim</p>
                <p className="text-gray-600">{new Date(data[data.length-1].timestamp).toLocaleString('pt-BR')}</p>
              </div>
            </Tooltip>
          </Marker>

          {/* Pontos intermediários */}
          {data.slice(1, -1).map((p, idx) => (
            <Marker key={idx} position={[p.latitude, p.longitude]} icon={routeIcon} />
          ))}
        </MapContainer>
      </div>

      {/* Estatísticas da rota */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-sm text-gray-500">Distância</p>
          <p className="text-lg font-bold">{totalDistance.toFixed(2)} km</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-sm text-gray-500">Duração</p>
          <p className="text-lg font-bold">{formatDuration(totalTime)}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-sm text-gray-500">Velocidade Média</p>
          <p className="text-lg font-bold">{avgSpeed.toFixed(1)} km/h</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-sm text-gray-500">Velocidade Máxima</p>
          <p className="text-lg font-bold">{maxSpeed.toFixed(1)} km/h</p>
        </div>
      </div>
    </div>
  )
}