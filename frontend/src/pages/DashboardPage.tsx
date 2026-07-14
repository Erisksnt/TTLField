import { useEffect, useMemo, useRef, useState } from 'react'
import { MapContainer, TileLayer, Marker, Tooltip, Circle, Popup, useMap, useMapEvents } from 'react-leaflet'
import { Icon, divIcon, Marker as LeafletMarker } from 'leaflet'
import { Link, useNavigate } from 'react-router-dom'
import Layout from '@/components/Layout'
import api from '@/services/api'
import { Technician, Geofence } from '@/types'
import { Loader, MapPin, AlertCircle, RefreshCw } from 'lucide-react'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useAuthStore } from '@/store/auth'

interface PositionData {
  latitude: number
  longitude: number
  speed?: number
  battery_level?: number
}

// Ícones individuais (online/offline)
const onlineIcon = new Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

const offlineIcon = new Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-grey.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

const CLUSTER_DISTANCE_METERS = 35
const EXPAND_ZOOM_THRESHOLD = 14

const getDistanceMeters = (lat1: number, lng1: number, lat2: number, lng2: number) => {
  const toRadians = (value: number) => (value * Math.PI) / 180
  const earthRadius = 6371000
  const dLat = toRadians(lat2 - lat1)
  const dLng = toRadians(lng2 - lng1)
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
    Math.sin(dLng / 2) * Math.sin(dLng / 2)

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return earthRadius * c
}

const createGroupKey = (technicians: Technician[]) => {
  const centerLat = technicians.reduce((sum, tech) => sum + (tech.latitude || 0), 0) / technicians.length
  const centerLng = technicians.reduce((sum, tech) => sum + (tech.longitude || 0), 0) / technicians.length
  const ids = technicians.map((tech) => tech.id).sort().join('-')
  return `${centerLat.toFixed(6)},${centerLng.toFixed(6)}:${ids}`
}

const getSpiderfiedPositions = (technicians: Technician[], centerLat: number, centerLng: number) => {
  const count = technicians.length
  const radius = Math.min(0.00045, 0.00008 + count * 0.00003)
  const angleStep = (2 * Math.PI) / count

  return technicians.map((tech, index) => {
    const angle = index * angleStep
    return {
      technician: tech,
      position: [centerLat + radius * Math.sin(angle), centerLng + radius * Math.cos(angle)] as [number, number],
    }
  })
}

function ClusterMapController({ onZoomChange }: { onZoomChange: (zoom: number) => void }) {
  useMapEvents({
    zoomend: (event) => onZoomChange(event.target.getZoom()),
  })

  return null
}

function MapFocusController({ focusTarget }: { focusTarget: { position: [number, number]; positions: [number, number][] } | null }) {
  const map = useMap()

  useEffect(() => {
    if (!focusTarget) return

    if (focusTarget.positions.length > 1) {
      map.fitBounds(focusTarget.positions, { padding: [48, 48], maxZoom: 17 })
      return
    }

    const bounds = map.getBounds()
    const isVisible = bounds.contains(focusTarget.position)
    const currentZoom = map.getZoom()

    if (!isVisible || currentZoom < 15) {
      map.flyTo(focusTarget.position, Math.max(currentZoom, 15), { duration: 0.7 })
    }
  }, [map, focusTarget])

  return null
}

const createTechnicianMarkerIcon = (technician: Technician) => {
  const initials = technician.name
    ?.split(' ')
    .map((word) => word[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() || '?'

  const background = technician.is_online ? '#dbeafe' : '#f3f4f6'
  const border = technician.is_online ? '#2563eb' : '#6b7280'
  const color = technician.is_online ? '#1d4ed8' : '#374151'

  return divIcon({
    className: 'technician-marker-icon',
    html: `
      <div style="
        width: 32px;
        height: 32px;
        border-radius: 9999px;
        background: ${background};
        border: 2px solid ${border};
        color: ${color};
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 13px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
      ">
        ${initials}
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16],
  })
}

// Função para criar ícone de grupo com número
const createGroupIcon = (count: number) => {
  return divIcon({
    className: 'custom-group-icon',
    html: `
      <div style="
        background-color: #9b59b6;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 14px;
        border: 2px solid white;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
      ">
        ${count}
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16],
  })
}

// Função para buscar endereço (com fallback)
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
  const past = new Date(date + 'Z')
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
  const [mapZoom, setMapZoom] = useState(12)
  const [selectedTechnicianId, setSelectedTechnicianId] = useState<string | null>(null)
  const [focusTarget, setFocusTarget] = useState<{ position: [number, number]; positions: [number, number][] } | null>(null)
  const markerRefs = useRef<Record<string, LeafletMarker | null>>({})
  const { lastPosition } = useWebSocket()
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)

  // Estado para controlar quais grupos estão expandidos
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set())

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

  useEffect(() => {
    if (mapZoom <= EXPAND_ZOOM_THRESHOLD) {
      setExpandedGroups(new Set())
    }
  }, [mapZoom])

  const handleRetryMap = () => {
    setMapError(false)
    setMapKey(prev => prev + 1)
  }

  const handleRefresh = () => {
    fetchTechnicians()
    fetchGeofences()
  }

  // Alternar expansão de um grupo
  const toggleGroup = (key: string) => {
    setExpandedGroups(prev => {
      const newSet = new Set(prev)
      if (newSet.has(key)) {
        newSet.delete(key)
      } else {
        newSet.add(key)
      }
      return newSet
    })
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

  const techniciansInsideGeofences = useMemo(() => {
    if (!geofences.length || !technicians.length) return 0

    const activeGeofences = geofences.filter(
      (geofence) =>
        geofence.is_active &&
        geofence.geofence_type === 'circle' &&
        geofence.center_latitude &&
        geofence.center_longitude &&
        geofence.radius
    )

    if (!activeGeofences.length) return 0

    const insideTechnicianIds = new Set<string>()

    technicians.forEach((tech) => {
      if (!tech.latitude || !tech.longitude) return

      const isInsideAnyGeofence = activeGeofences.some((geofence) => {
        const centerLat = parseFloat(geofence.center_latitude!)
        const centerLng = parseFloat(geofence.center_longitude!)
        const radius = Number(geofence.radius || 0)
        const distance = getDistanceMeters(tech.latitude!, tech.longitude!, centerLat, centerLng)
        return distance <= radius
      })

      if (isInsideAnyGeofence) {
        insideTechnicianIds.add(tech.id)
      }
    })

    return insideTechnicianIds.size
  }, [geofences, technicians])

  const groupedPositions = useMemo(() => {
    const groups: Array<{ key: string; center: [number, number]; technicians: Technician[] }> = []
    const allWithLocation = technicians.filter((t) => t.latitude && t.longitude)
    const visited = new Set<string>()

    allWithLocation.forEach((tech) => {
      if (visited.has(tech.id)) return

      const cluster: Technician[] = [tech]
      visited.add(tech.id)

      allWithLocation.forEach((candidate) => {
        if (visited.has(candidate.id) || candidate.id === tech.id) return

        const distance = getDistanceMeters(
          tech.latitude!,
          tech.longitude!,
          candidate.latitude!,
          candidate.longitude!
        )

        if (distance <= CLUSTER_DISTANCE_METERS) {
          cluster.push(candidate)
          visited.add(candidate.id)
        }
      })

      const centerLat = cluster.reduce((sum, item) => sum + (item.latitude || 0), 0) / cluster.length
      const centerLng = cluster.reduce((sum, item) => sum + (item.longitude || 0), 0) / cluster.length

      groups.push({
        key: createGroupKey(cluster),
        center: [centerLat, centerLng],
        technicians: cluster,
      })
    })

    return groups
  }, [technicians])

  const handleTechnicianSelect = (technician: Technician) => {
    if (!technician.latitude || !technician.longitude) return

    const matchingGroup = groupedPositions.find((group) =>
      group.technicians.some((item) => item.id === technician.id)
    )

    setSelectedTechnicianId(technician.id)
    setFocusTarget({
      position: [technician.latitude, technician.longitude],
      positions: matchingGroup && matchingGroup.technicians.length > 1
        ? matchingGroup.technicians.map((item) => [item.latitude!, item.longitude!] as [number, number])
        : [[technician.latitude, technician.longitude]],
    })

    if (matchingGroup && matchingGroup.technicians.length > 1) {
      setExpandedGroups((prev) => {
        const next = new Set(prev)
        next.add(matchingGroup.key)
        return next
      })
    }
  }

  useEffect(() => {
    if (!selectedTechnicianId) return

    const marker = markerRefs.current[selectedTechnicianId]
    if (marker) {
      marker.openPopup()
    }
  }, [selectedTechnicianId, groupedPositions, expandedGroups])

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600">Monitoramento em tempo real</p>
          </div>
          <button
            onClick={handleRefresh}
            className="flex items-center gap-1 md:gap-2 bg-gray-500 hover:bg-gray-600 text-white font-semibold py-1.5 md:py-2 px-3 md:px-4 rounded-lg transition text-sm md:text-base"
          >
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
            <h3 className="text-gray-600 text-sm font-medium">Usuarios em Geofences</h3>
            <p className="text-3xl font-bold text-gray-900 mt-2">{techniciansInsideGeofences}</p>
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
                style={{ height: '100%', width: '100%', zIndex: 1 }}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  eventHandlers={{ error: () => setMapError(true) }}
                />
                <ClusterMapController onZoomChange={setMapZoom} />
                <MapFocusController focusTarget={focusTarget} />

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

                {/* Marcadores agrupados e individuais */}
                {groupedPositions.map(({ key, center, technicians: techs }) => {
                  const [lat, lng] = center
                  const isGroup = techs.length > 1
                  const isExpanded = expandedGroups.has(key)

                  if (isGroup && isExpanded) {
                    return getSpiderfiedPositions(techs, lat, lng).map(({ technician, position }) => {
                      const icon = createTechnicianMarkerIcon(technician)

                      return (
                        <Marker
                          key={`${key}-${technician.id}`}
                          ref={(instance) => {
                            markerRefs.current[technician.id] = instance
                          }}
                          position={position}
                          icon={icon}
                          eventHandlers={{
                            click: () => {
                              setSelectedTechnicianId(technician.id)
                              setFocusTarget({ position, positions: [position] })
                            },
                          }}
                        >
                          <Popup>
                            <TechnicianPopup technician={technician} address={addresses[technician.id]} />
                          </Popup>
                        </Marker>
                      )
                    })
                  }

                  const icon = isGroup
                    ? createGroupIcon(techs.length)
                    : createTechnicianMarkerIcon(techs[0])

                  return (
                    <Marker
                      key={key}
                      ref={(instance) => {
                        if (isGroup) return
                        markerRefs.current[techs[0].id] = instance
                      }}
                      position={[lat, lng]}
                      icon={icon}
                      eventHandlers={{
                        click: () => {
                          setFocusTarget({
                            position: [lat, lng],
                            positions: isGroup ? techs.map((tech) => [tech.latitude!, tech.longitude!] as [number, number]) : [[lat, lng]],
                          })
                          if (isGroup) {
                            toggleGroup(key)
                          }
                        }
                      }}
                    >
                      <Popup>
                        {isGroup ? (
                          <div className="text-sm max-w-xs">
                            <p className="font-semibold text-gray-700 mb-2">🟣 {techs.length} técnicos nesta localização</p>
                            <p className="text-xs text-gray-500 mb-2">Clique no marcador para expandir ou recolher</p>
                            <div className="max-h-60 overflow-y-auto space-y-2">
                              {techs.map((tech) => (
                                <div key={tech.id} className="flex items-center justify-between py-1 border-b last:border-0">
                                  <div>
                                    <p className="font-medium text-gray-900">{tech.name}</p>
                                    <p className="text-xs text-gray-500">{tech.employee_id}</p>
                                    <p className="text-xs text-gray-500">Bateria: {tech.battery_level || 'N/A'}%</p>
                                  </div>
                                  <Link
                                    to={`/reports?technicianId=${tech.id}`}
                                    className="ml-2 text-blue-600 hover:text-blue-800 text-xs font-medium whitespace-nowrap"
                                  >
                                    📊 Relatório
                                  </Link>
                                </div>
                              ))}
                            </div>
                          </div>
                        ) : (
                          <TechnicianPopup technician={techs[0]} address={addresses[techs[0].id]} />
                        )}
                      </Popup>
                    </Marker>
                  )
                })}
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
                <button
                  key={technician.id}
                  type="button"
                  onClick={() => handleTechnicianSelect(technician)}
                  className="flex w-full items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition text-left"
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-900">{technician.name}</p>
                    <p className="text-sm text-gray-600">{technician.employee_id}</p>
                    {addresses[technician.id] && (
                      <p className="text-xs text-gray-500 mt-1 break-words" title={addresses[technician.id]}>
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
                </button>
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
                <button
                  key={technician.id}
                  type="button"
                  onClick={() => handleTechnicianSelect(technician)}
                  className="flex w-full items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition text-left"
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-900">{technician.name}</p>
                    <p className="text-sm text-gray-600">{technician.employee_id}</p>
                    {addresses[technician.id] && (
                      <p className="text-xs text-gray-500 mt-1 break-words" title={addresses[technician.id]}>
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
                </button>
              ))
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}

function TechnicianPopup({ technician, address }: { technician: Technician; address?: string }) {
  const navigate = useNavigate()

  return (
    <div className="text-sm max-w-xs rounded-lg border border-gray-200 bg-white p-3 shadow-sm">
      <div className="space-y-2">
        <div>
          <p className="font-semibold text-gray-900">{technician.name}</p>
          <p className="text-gray-600 text-sm">{technician.employee_id}</p>
        </div>
        <div className="text-gray-600 text-sm space-y-1">
          <p>Endereço: {address || `${technician.latitude?.toFixed(4) || 'N/A'}, ${technician.longitude?.toFixed(4) || 'N/A'}`}</p>
          <p>Bateria: {technician.battery_level || 'N/A'}%</p>
          <p>Últ. GPS: {timeAgo(technician.last_seen)}</p>
        </div>
        <p className={`text-xs font-medium ${technician.is_online ? 'text-green-600' : 'text-gray-500'}`}>
          {technician.is_online ? '🟢 Online' : '🔴 Offline'}
        </p>
        <button
          type="button"
          onClick={() => navigate(`/reports?technicianId=${technician.id}`)}
          className="w-full mt-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium px-3 py-2 rounded transition"
        >
          Ver relatórios
        </button>
      </div>
    </div>
  )
}