// frontend/src/components/reports/RouteTab.tsx
import { MapContainer, TileLayer, Polyline, Marker, Tooltip } from 'react-leaflet'
import { Icon } from 'leaflet'
import { Fragment } from 'react'

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
  journey_index?: number | null
  is_journey_start?: boolean
  is_journey_end?: boolean
  segment_distance_km?: number
  segment_time_seconds?: number
  segment_speed_kmh?: number
}

interface RouteTabProps {
  data?: RoutePoint[]
}

const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${Math.round(seconds)}s`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}min`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins === 0 ? `${hours}h` : `${hours}h ${mins}min`
}

const formatDateTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleString('pt-BR', {
    timeZone: 'America/Sao_Paulo',
  })
}

export default function RouteTab({ data }: RouteTabProps) {
  if (!data || data.length < 2) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p className="text-lg">Nenhuma rota encontrada para o periodo selecionado</p>
        <p className="text-sm mt-1">Selecione um tecnico e um periodo com pelo menos duas posicoes registradas.</p>
      </div>
    )
  }

  const journeys = data.reduce((acc, point) => {
    const key = point.journey_index ?? 0
    if (!acc[key]) acc[key] = []
    acc[key].push(point)
    return acc
  }, {} as Record<number, RoutePoint[]>)

  const journeyEntries = Object.entries(journeys)
    .map(([journeyIndex, points]) => ({ journeyIndex: Number(journeyIndex), points }))
    .filter((journey) => journey.points.length >= 2)

  const centerLat = data.reduce((sum, point) => sum + point.latitude, 0) / data.length
  const centerLng = data.reduce((sum, point) => sum + point.longitude, 0) / data.length

  let totalDistance = 0
  let totalTime = 0
  let maxSpeed = 0

  data.forEach((point) => {
    const distance = point.segment_distance_km ?? 0
    const time = point.segment_time_seconds ?? 0
    const speed = point.segment_speed_kmh ?? 0
    totalDistance += distance
    totalTime += time
    if (speed > maxSpeed) maxSpeed = speed
  })

  const avgSpeed = totalTime > 0 ? (totalDistance / totalTime) * 3600 : 0

  return (
    <div>
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
        <p className="text-sm text-blue-700">
          <strong>Rota percorrida</strong> - {data.length} pontos em {journeyEntries.length} viagem(ns).
          Distancia total: <strong>{totalDistance.toFixed(2)} km</strong>
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

          {journeyEntries.map(({ journeyIndex, points }) => {
            const positions: [number, number][] = points.map(point => [point.latitude, point.longitude])
            const start = points[0]
            const end = points[points.length - 1]
            const label = journeyIndex > 0 ? `Viagem ${journeyIndex}` : 'Viagem'

            return (
              <Fragment key={journeyIndex}>
                <Polyline
                  positions={positions}
                  color="#3b82f6"
                  weight={4}
                  opacity={0.8}
                />

                <Marker position={[start.latitude, start.longitude]} icon={startIcon}>
                  <Tooltip sticky>
                    <div className="text-sm">
                      <p className="font-semibold text-green-700">Inicio - {label}</p>
                      <p className="text-gray-600">{formatDateTime(start.timestamp)}</p>
                    </div>
                  </Tooltip>
                </Marker>

                <Marker position={[end.latitude, end.longitude]} icon={endIcon}>
                  <Tooltip sticky>
                    <div className="text-sm">
                      <p className="font-semibold text-red-700">Fim - {label}</p>
                      <p className="text-gray-600">{formatDateTime(end.timestamp)}</p>
                    </div>
                  </Tooltip>
                </Marker>
              </Fragment>
            )
          })}
        </MapContainer>
      </div>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-sm text-gray-500">Distancia</p>
          <p className="text-lg font-bold">{totalDistance.toFixed(2)} km</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-sm text-gray-500">Tempo em movimento</p>
          <p className="text-lg font-bold">{formatDuration(totalTime)}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-sm text-gray-500">Velocidade Media</p>
          <p className="text-lg font-bold">{avgSpeed.toFixed(1)} km/h</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-sm text-gray-500">Velocidade Maxima</p>
          <p className="text-lg font-bold">{maxSpeed.toFixed(1)} km/h</p>
        </div>
      </div>
    </div>
  )
}
