import { MapContainer, TileLayer, Polyline, Marker, Tooltip } from 'react-leaflet'
import { Icon, latLngBounds } from 'leaflet'
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
  // `data` may be either the legacy RoutePoint[] or the new backend response
  data?: any
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

const formatTimeOnly = (timestamp: string): string => {
  return new Date(timestamp).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
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
  // Modo de visualização da rota no mapa
  const [viewMode, setViewMode] = useState<'combined' | 'individual'>('combined')
  // Flag para carregamento dos endereços
  const [loadingAddresses, setLoadingAddresses] = useState(false)

  // --- PROCESSAMENTO DOS DADOS ---
  useEffect(() => {
    const rawData: RoutePoint[] = Array.isArray(data) ? (data as RoutePoint[]) : (data?.route as RoutePoint[]) || []
    if (!rawData || rawData.length < 2) {
      setTrips([])
      setSelectedTrips(new Set())
      return
    }

    // Agrupar pontos por journey_index
    const journeys = rawData.reduce((acc: Record<number, RoutePoint[]>, point: RoutePoint) => {
      const key = point.journey_index ?? 0
      if (!acc[key]) acc[key] = []
      acc[key].push(point)
      return acc
    }, {} as Record<number, RoutePoint[]>)

    // Converter para array e filtrar viagens com pelo menos 2 pontos
    const journeyEntries = Object.entries(journeys)
      .map(([journeyIndex, points]) => ({
        journeyIndex: Number(journeyIndex),
        points: points as RoutePoint[],
        startPoint: points[0] as RoutePoint,
        endPoint: points[points.length - 1] as RoutePoint,
        startAddress: undefined,
        endAddress: undefined,
        loadingAddress: true,
      }))
      .filter((journey) => journey.points.length >= 2)

    // Ordenar por journeyIndex (cronológico)
    journeyEntries.sort((a, b) => a.journeyIndex - b.journeyIndex)

    // Inicializar estado com loading
    setTrips(journeyEntries)
    // Selecionar todas por padrão e exibir a rota completa
    setSelectedTrips(new Set(journeyEntries.map((t) => t.journeyIndex)))
    setViewMode('combined')

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
      setSelectedTrips(new Set())
      setViewMode('individual')
    } else {
      setSelectedTrips(new Set(trips.map((t) => t.journeyIndex)))
      setViewMode('combined')
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

  const getRoutePositions = (journey: { points: RoutePoint[]; journeyIndex: number }) => {
    const rawPositions: [number, number][] = journey.points.map((point) => [point.latitude, point.longitude] as [number, number])
    const matchedMap = Array.isArray(data) ? undefined : (data?.matched_routes || {})
    const matchedPositions = matchedMap ? matchedMap[journey.journeyIndex] : undefined
    return matchedPositions && matchedPositions.length >= 2 ? matchedPositions : rawPositions
  }

  const routePositions = useMemo((): [number, number][] => {
    return visibleJourneys.flatMap((journey) => getRoutePositions(journey))
  }, [visibleJourneys, data])

  const routeBounds = useMemo(() => {
    if (routePositions.length === 0) return undefined
    return latLngBounds(routePositions)
  }, [routePositions])

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
      {/* MAPA */}
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="text-sm font-medium text-gray-700">Visualização da rota</div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => {
              setViewMode('combined')
              setSelectedTrips(new Set(trips.map((trip) => trip.journeyIndex)))
            }}
            className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
              viewMode === 'combined' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Rota combinada
          </button>
          <button
            type="button"
            onClick={() => setViewMode('individual')}
            className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
              viewMode === 'individual' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Viagens individuais
          </button>
        </div>
      </div>

      <div className="h-96 rounded-lg overflow-hidden border">
        <MapContainer
          center={[center.lat, center.lng]}
          bounds={routeBounds}
          zoom={14}
          style={{ height: '100%', width: '100%', zIndex: 1 }}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; OpenStreetMap contributors'
          />

          {viewMode === 'combined' ? (
            <Fragment>
              <Polyline positions={routePositions} color="#3b82f6" weight={4} opacity={0.8} />
              {visibleJourneys.length > 0 && (
                <Fragment>
                  <Marker position={[visibleJourneys[0].startPoint.latitude, visibleJourneys[0].startPoint.longitude]} icon={startIcon}>
                    <Tooltip sticky>
                      <div className="text-sm">
                        <p className="font-semibold text-green-700">Início</p>
                        <p className="text-gray-600">{formatDateTime(visibleJourneys[0].startPoint.timestamp)}</p>
                      </div>
                    </Tooltip>
                  </Marker>

                  <Marker position={[visibleJourneys[visibleJourneys.length - 1].endPoint.latitude, visibleJourneys[visibleJourneys.length - 1].endPoint.longitude]} icon={endIcon}>
                    <Tooltip sticky>
                      <div className="text-sm">
                        <p className="font-semibold text-red-700">Fim</p>
                        <p className="text-gray-600">{formatDateTime(visibleJourneys[visibleJourneys.length - 1].endPoint.timestamp)}</p>
                      </div>
                    </Tooltip>
                  </Marker>
                </Fragment>
              )}
            </Fragment>
          ) : (
            visibleJourneys.map(({ journeyIndex, points, startPoint, endPoint }) => {
              const positions = getRoutePositions({ journeyIndex, points })
              const sequentialIndex = trips.findIndex((t) => t.journeyIndex === journeyIndex) + 1
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
            })
          )}
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
                    </div>
                    <div className="mt-1 text-xs text-gray-500">
                      {formatTimeOnly(trip.startPoint.timestamp)} → {formatTimeOnly(trip.endPoint.timestamp)}
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