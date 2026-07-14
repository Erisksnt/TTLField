// frontend/src/components/reports/GeofenceTab.tsx
import { useEffect, useRef, useState } from 'react'
import { MapContainer, TileLayer, Marker, Tooltip, Popup, useMap } from 'react-leaflet'
import { Icon, type Marker as LeafletMarker } from 'leaflet'
import { Clock, MapPin, ArrowRight, ArrowLeft } from 'lucide-react'

// Ícone para pontos de parada
const stopIcon = new Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

const selectedStopIcon = new Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

// Ícone para entrada em geofence (verde)
const enterIcon = new Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

// Ícone para saída de geofence (laranja)
const exitIcon = new Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

interface GeofenceEvent {
  geofence_name: string
  event_type: 'enter' | 'exit'
  timestamp: string
  latitude: number
  longitude: number
}

interface StopPoint {
  latitude: number
  longitude: number
  start_time: string
  end_time: string
  duration_minutes: number
  address?: string | null
}

interface GeofenceTabProps {
  data?: GeofenceEvent[]
  stops?: StopPoint[]
}

function getPopupOffsetPosition(map: any, position: [number, number], popupOffsetPixels = 180): [number, number] {
  const zoom = map.getZoom()
  const point = map.project(position, zoom)
  point.y -= popupOffsetPixels
  return map.unproject(point, zoom)
}

function MapFocusController({ position, popupOffsetPixels = 180 }: { position: [number, number] | null; popupOffsetPixels?: number }) {
  const map = useMap()

  useEffect(() => {
    if (!position) return

    const targetPosition = getPopupOffsetPosition(map, position, popupOffsetPixels)
    map.flyTo(targetPosition, map.getZoom(), { duration: 0.7 })
  }, [map, position, popupOffsetPixels])

  return null
}

export default function GeofenceTab({ data, stops }: GeofenceTabProps) {
  const [selectedStopIndex, setSelectedStopIndex] = useState<number | null>(null)
  const [focusedPosition, setFocusedPosition] = useState<[number, number] | null>(null)

  const stopMarkersRef = useRef<Record<number, LeafletMarker | null>>({})

  const hasGeofenceEvents = Boolean(data && data.length > 0)
  const hasStops = Boolean(stops && stops.length > 0)

  if (!hasGeofenceEvents && !hasStops) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p className="text-lg">Nenhum evento de geofence ou parada encontrado para o período selecionado</p>
      </div>
    )
  }

  // Formatar data/hora
  const formatTime = (isoString: string) => {
    const date = new Date(isoString)
    return date.toLocaleString('pt-BR', {
      timeZone: 'America/Sao_Paulo',
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // Formatar duração
  const formatDuration = (minutes: number) => {
    if (minutes < 1) return `${Math.round(minutes * 60)}s`
    if (minutes < 60) return `${Math.round(minutes)}min`
    const hours = Math.floor(minutes / 60)
    const mins = Math.round(minutes % 60)
    return `${hours}h ${mins}min`
  }

  // Agrupar eventos por geofence para exibição na lista
  const eventsByGeofence = (data ?? []).reduce((acc, event) => {
    const key = event.geofence_name
    if (!acc[key]) acc[key] = []
    acc[key].push(event)
    return acc
  }, {} as Record<string, GeofenceEvent[]>)

  // Calcular centro do mapa com base nos eventos ou paradas
  const centerLat = hasGeofenceEvents
    ? data!.reduce((sum, e) => sum + e.latitude, 0) / data!.length
    : stops!.reduce((sum, stop) => sum + stop.latitude, 0) / stops!.length
  const centerLng = hasGeofenceEvents
    ? data!.reduce((sum, e) => sum + e.longitude, 0) / data!.length
    : stops!.reduce((sum, stop) => sum + stop.longitude, 0) / stops!.length

  const handleStopClick = (stop: StopPoint, index: number) => {
    if (stop.latitude == null || stop.longitude == null) return
    setSelectedStopIndex(index)
    setFocusedPosition([stop.latitude, stop.longitude])

    const marker = stopMarkersRef.current[index]
    if (marker && marker.openPopup) {
      marker.openPopup()
    }
  }

  const handleGeofenceEventClick = (event: GeofenceEvent) => {
    setFocusedPosition([event.latitude, event.longitude])
  }

  return (
    <div>
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
        <p className="text-sm text-blue-700">
          <strong>Eventos de Geofence</strong> - {hasGeofenceEvents ? `${data!.length} evento(s) registrado(s) no período.` : 'Nenhum evento de geofence encontrado no período.'}
          {hasStops && ` • ${stops!.length} parada(s) identificada(s).`}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Mapa */}
        <div className="lg:col-span-2 h-96 rounded-lg overflow-hidden border">
          <MapContainer
            center={[centerLat || -23.515, centerLng || -46.865]}
            zoom={14}
            style={{ height: '100%', width: '100%', zIndex: 1 }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; OpenStreetMap contributors'
            />

            <MapFocusController position={focusedPosition} />

            {/* Eventos de Geofence (entrada/saída) */}
            {(data ?? []).map((event, index) => {
              const icon = event.event_type === 'enter' ? enterIcon : exitIcon
              const label = event.event_type === 'enter' ? 'Entrada' : 'Saída'
              return (
                <Marker
                  key={`${event.geofence_name}-${index}`}
                  position={[event.latitude, event.longitude]}
                  icon={icon}
                  eventHandlers={{ click: () => handleGeofenceEventClick(event) }}
                >
                  <Tooltip sticky>
                    <div className="text-sm">
                      <p className="font-semibold">{event.geofence_name}</p>
                      <p className="text-gray-600">{label} em {formatTime(event.timestamp)}</p>
                    </div>
                  </Tooltip>
                </Marker>
              )
            })}

            {/* Paradas */}
            {stops && stops.map((stop, index) => (
              <Marker
                key={`stop-${index}`}
                position={[stop.latitude, stop.longitude]}
                icon={selectedStopIndex === index ? selectedStopIcon : stopIcon}
                ref={(marker) => {
                  stopMarkersRef.current[index] = marker as LeafletMarker | null
                }}
                eventHandlers={{ click: () => handleStopClick(stop, index) }}
              >
                <Tooltip sticky>
                  <div className="text-sm">
                    <p className="font-semibold">⏸️ Parada</p>
                    <p className="text-gray-600">Duração: {formatDuration(stop.duration_minutes)}</p>
                    <p className="text-xs text-gray-500">
                      {formatTime(stop.start_time)} - {formatTime(stop.end_time)}
                    </p>
                  </div>
                </Tooltip>
                <Popup>
                  <StopPopup stop={stop} index={index} />
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>

        {/* Lista de eventos */}
        <div className="bg-white rounded-lg border p-4 max-h-96 overflow-y-auto">
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <MapPin className="w-4 h-4 text-blue-500" />
            Eventos de Geofence
          </h3>
          <div className="space-y-3">
            {Object.entries(eventsByGeofence).map(([name, events]) => (
              <div key={name} className="border rounded-lg p-2">
                <p className="font-medium text-sm text-gray-900">{name}</p>
                {events.map((event, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleGeofenceEventClick(event)}
                    className="flex w-full items-center gap-2 text-xs text-gray-600 mt-1 text-left hover:text-blue-600"
                  >
                    {event.event_type === 'enter' ? (
                      <ArrowRight className="w-3 h-3 text-green-600" />
                    ) : (
                      <ArrowLeft className="w-3 h-3 text-orange-600" />
                    )}
                    <span>{event.event_type === 'enter' ? 'Entrada' : 'Saída'}</span>
                    <span>•</span>
                    <span>{formatTime(event.timestamp)}</span>
                  </button>
                ))}
              </div>
            ))}
          </div>

          {stops && stops.length > 0 && (
            <>
              <h3 className="font-semibold text-gray-900 mt-4 mb-3 flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-500" />
                Posições de Parada ({stops.length})
              </h3>
              <div className="space-y-2">
                {stops.map((stop, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => handleStopClick(stop, index)}
                    className="w-full text-left flex items-center justify-between p-2 border rounded-lg hover:bg-gray-50"
                  >
                    <div>
                      <p className="text-sm font-medium">Parada {index + 1}</p>
                      <p className="text-xs text-gray-500">
                        {formatTime(stop.start_time)} - {formatTime(stop.end_time)}
                      </p>
                      <p className="text-xs text-gray-500">
                        Duração: {formatDuration(stop.duration_minutes)}
                      </p>
                      <p className="text-xs text-gray-500 max-w-[180px] truncate">
                        Address: {stop.address || "Address unavailable"}
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function StopPopup({ stop, index }: { stop: StopPoint; index: number }) {
  const formatTime = (isoString: string) => {
    const date = new Date(isoString)
    return date.toLocaleString('pt-BR', {
      timeZone: 'America/Sao_Paulo',
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatDuration = (minutes: number) => {
    if (minutes < 1) return `${Math.round(minutes * 60)}s`
    if (minutes < 60) return `${Math.round(minutes)}min`
    const hours = Math.floor(minutes / 60)
    const mins = Math.round(minutes % 60)
    return `${hours}h ${mins}min`
  }

  return (
    <div className="text-sm max-w-xs rounded-lg border border-gray-200 bg-white p-3 shadow-sm">
      <div className="space-y-2">
        <div>
          <p className="font-semibold text-gray-900">Parada {index + 1}</p>
        </div>
        <div className="text-gray-600 text-sm space-y-1">
          <p>Duração: {formatDuration(stop.duration_minutes)}</p>
          <p>{formatTime(stop.start_time)} - {formatTime(stop.end_time)}</p>
          <p>Endereço: {stop.address || 'Indisponível'}</p>
        </div>
      </div>
    </div>
  )
}
