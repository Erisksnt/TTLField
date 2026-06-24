import { MapContainer, TileLayer, Polyline, Marker, Tooltip } from 'react-leaflet'
import { Icon } from 'leaflet'
import { Fragment, useState, useEffect, useMemo } from 'react'

// Ícones para os marcadores
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

// Tipos
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

// Utilitários
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

// Função para obter endereço via Nominatim (geocodificação reversa)
async function fetchAddress(lat: number, lng: number): Promise<string> {
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`
    )
    const data = await res.json()
    return data.display_name || 'Endereço não encontrado'
  } catch (error) {
    console.error('Erro ao buscar endereço:', error)
    return 'Endereço indisponível'
  }
}

export default function RouteTab({ data }: RouteTabProps) {
  // --- ESTADOS ---
  // Dados processados de cada viagem
  const [trips, setTrips] = useState<
    Array<{
      journeyIndex: number
      points: RoutePoint[]
      startPoint: RoutePoint
      endPoint: RoutePoint
      startAddress?: string
      endAddress?: string
      loadingAddress?: boolean
    }>
  >([])
  // Conjunto dos índices das viagens selecionadas (exibidas no mapa)
  const [selectedTrips, setSelectedTrips] = useState<Set<number>>(new Set())
  // Flag para carregamento dos endereços
  const [loadingAddresses, setLoadingAddresses] = useState(false)

  // --- PROCESSAMENTO DOS DADOS ---
  useEffect(() => {
    if (!data || data.length < 2) {
      setTrips([])
      setSelectedTrips(new Set())
      return
    }

    // Agrupar pontos por journey_index
    const journeys = data.reduce((acc, point) => {
      const key = point.journey_index ?? 0
      if (!acc[key]) acc[key] = []
      acc[key].push(point)
      return acc
    }, {} as Record<number, RoutePoint[]>)

    // Converter para array e filtrar viagens com pelo menos 2 pontos
    const journeyEntries = Object.entries(journeys)
      .map(([journeyIndex, points]) => ({
        journeyIndex: Number(journeyIndex),
        points,
        startPoint: points[0],
        endPoint: points[points.length - 1],
        startAddress: undefined,
        endAddress: undefined,
        loadingAddress: true,
      }))
      .filter((journey) => journey.points.length >= 2)

    // Ordenar por journeyIndex (cronológico)
    journeyEntries.sort((a, b) => a.journeyIndex - b.journeyIndex)

    // Inicializar estado com loading
    setTrips(journeyEntries)
    // Selecionar todas por padrão
    setSelectedTrips(new Set(journeyEntries.map((t) => t.journeyIndex)))

    // Buscar endereços para cada viagem
    setLoadingAddresses(true)
    const fetchAddresses = async () => {
      const updatedTrips = await Promise.all(
        journeyEntries.map(async (trip) => {
          const [startAddr, endAddr] = await Promise.all([
            fetchAddress(trip.startPoint.latitude, trip.startPoint.longitude),
            fetchAddress(trip.endPoint.latitude, trip.endPoint.longitude),
          ])
          return {
            ...trip,
            startAddress: startAddr,
            endAddress: endAddr,
            loadingAddress: false,
          }
        })
      )
      setTrips(updatedTrips)
      setLoadingAddresses(false)
    }
    fetchAddresses()
  }, [data])

  // --- FUNÇÕES DE CONTROLE DOS CHECKBOXES ---
  const toggleTrip = (journeyIndex: number) => {
    setSelectedTrips((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(journeyIndex)) {
        newSet.delete(journeyIndex)
      } else {
        newSet.add(journeyIndex)
      }
      return newSet
    })
  }

  const toggleAll = () => {
    if (selectedTrips.size === trips.length) {
      setSelectedTrips(new Set()) // desmarca todos
    } else {
      setSelectedTrips(new Set(trips.map((t) => t.journeyIndex))) // marca todos
    }
  }

  // --- FILTRAR VIAGENS VISÍVEIS NO MAPA ---
  const visibleJourneys = useMemo(() => {
    return trips.filter((trip) => selectedTrips.has(trip.journeyIndex))
  }, [trips, selectedTrips])

  // --- CÁLCULO DAS ESTATÍSTICAS (apenas viagens visíveis) ---
  const stats = useMemo(() => {
    let totalDistance = 0
    let totalTime = 0
    let maxSpeed = 0
    const visiblePoints = visibleJourneys.flatMap((j) => j.points)
    visiblePoints.forEach((point) => {
      const distance = point.segment_distance_km ?? 0
      const time = point.segment_time_seconds ?? 0
      const speed = point.segment_speed_kmh ?? 0
      totalDistance += distance
      totalTime += time
      if (speed > maxSpeed) maxSpeed = speed
    })
    const avgSpeed = totalTime > 0 ? (totalDistance / totalTime) * 3600 : 0
    return { totalDistance, totalTime, maxSpeed, avgSpeed, totalPoints: visiblePoints.length }
  }, [visibleJourneys])

  // --- CENTRO DO MAPA (baseado nas viagens visíveis) ---
  const center = useMemo(() => {
    if (visibleJourneys.length === 0) {
      return { lat: -23.5505, lng: -46.6333 } // fallback São Paulo
    }
    const points = visibleJourneys.flatMap((j) => j.points)
    const lat = points.reduce((sum, p) => sum + p.latitude, 0) / points.length
    const lng = points.reduce((sum, p) => sum + p.longitude, 0) / points.length
    return { lat, lng }
  }, [visibleJourneys])

  // --- RENDERIZAÇÃO ---
  if (!data || data.length < 2) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p className="text-lg">Nenhuma rota encontrada para o período selecionado</p>
        <p className="text-sm mt-1">Selecione um técnico e um período com pelo menos duas posições registradas.</p>
      </div>
    )
  }

  if (trips.length === 0) {
    return <div className="text-center py-12 text-gray-500">Carregando dados...</div>
  }

  return (
    <div>
      {/* Resumo das viagens visíveis */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
        <p className="text-sm text-blue-700">
          <strong>Rota percorrida</strong> - {stats.totalPoints} pontos em {visibleJourneys.length} viagem(ns).
          Distância total: <strong>{stats.totalDistance.toFixed(2)} km</strong>
        </p>
      </div>

      {/* MAPA */}
      <div className="h-96 rounded-lg overflow-hidden border">
        <MapContainer
          center={[center.lat, center.lng]}
          zoom={14}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; OpenStreetMap contributors'
          />

          {visibleJourneys.map(({ journeyIndex, points, startPoint, endPoint }) => {
            const positions: [number, number][] = points.map((p) => [p.latitude, p.longitude])
            // Encontra o índice sequencial (posição no array trips) para exibir numeração correta
            const sequentialIndex = trips.findIndex(t => t.journeyIndex === journeyIndex) + 1
            const label = `Viagem ${sequentialIndex}`

            return (
              <Fragment key={journeyIndex}>
                <Polyline positions={positions} color="#3b82f6" weight={4} opacity={0.8} />

                <Marker position={[startPoint.latitude, startPoint.longitude]} icon={startIcon}>
                  <Tooltip sticky>
                    <div className="text-sm">
                      <p className="font-semibold text-green-700">Início - {label}</p>
                      <p className="text-gray-600">{formatDateTime(startPoint.timestamp)}</p>
                    </div>
                  </Tooltip>
                </Marker>

                <Marker position={[endPoint.latitude, endPoint.longitude]} icon={endIcon}>
                  <Tooltip sticky>
                    <div className="text-sm">
                      <p className="font-semibold text-red-700">Fim - {label}</p>
                      <p className="text-gray-600">{formatDateTime(endPoint.timestamp)}</p>
                    </div>
                  </Tooltip>
                </Marker>
              </Fragment>
            )
          })}
        </MapContainer>
      </div>

      {/* LISTA DE VIAGENS COM CHECKBOXES */}
      <div className="mt-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-800">Viagens</h3>
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              checked={selectedTrips.size === trips.length && trips.length > 0}
              onChange={toggleAll}
              className="w-4 h-4 text-blue-600"
            />
            Selecionar todas
          </label>
        </div>

        {loadingAddresses ? (
          <div className="text-gray-500 text-sm">Carregando endereços...</div>
        ) : (
          <div className="space-y-2 max-h-80 overflow-y-auto border rounded-lg p-2">
            {trips.map((trip, idx) => {
              const isChecked = selectedTrips.has(trip.journeyIndex)
              return (
                <div
                  key={trip.journeyIndex}
                  className={`flex items-start gap-3 p-2 rounded-lg transition ${
                    isChecked ? 'bg-blue-50' : 'bg-gray-50'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => toggleTrip(trip.journeyIndex)}
                    className="mt-1 w-4 h-4 text-blue-600"
                  />
                  <div className="flex-1 text-sm">
                    <div className="font-medium text-gray-800">
                      Viagem {idx + 1}
                      <span className="ml-2 text-xs text-gray-500">
                        {trip.points.length} pontos
                      </span>
                    </div>
                    <div className="text-gray-600">
                      <span className="font-semibold text-green-600">Saída:</span>{' '}
                      {trip.startAddress || '...'}
                    </div>
                    <div className="text-gray-600">
                      <span className="font-semibold text-red-600">Chegada:</span>{' '}
                      {trip.endAddress || '...'}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* ESTATÍSTICAS (apenas viagens visíveis) */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-sm text-gray-500">Distância</p>
          <p className="text-lg font-bold">{stats.totalDistance.toFixed(2)} km</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-sm text-gray-500">Tempo em movimento</p>
          <p className="text-lg font-bold">{formatDuration(stats.totalTime)}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-sm text-gray-500">Velocidade Média</p>
          <p className="text-lg font-bold">{stats.avgSpeed.toFixed(1)} km/h</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-sm text-gray-500">Velocidade Máxima</p>
          <p className="text-lg font-bold">{stats.maxSpeed.toFixed(1)} km/h</p>
        </div>
      </div>
    </div>
  )
}