// frontend/src/components/reports/GeofenceTab.tsx
import { MapContainer, TileLayer, Circle, Marker, Tooltip } from 'react-leaflet'
import { Icon } from 'leaflet'
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
}

interface GeofenceTabProps {
  data?: GeofenceEvent[]
  stops?: StopPoint[]
}

export default function GeofenceTab({ data, stops }: GeofenceTabProps) {
  // Se não houver dados, exibe mensagem
  if (!data || data.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p className="text-lg">📍 Nenhum evento de geofence encontrado para o período selecionado</p>
      </div>
    )
  }

  // Formatar data/hora
  const formatTime = (isoString: string) => {
    const date = new Date(isoString)
    return date.toLocaleString('pt-BR', {
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
  const eventsByGeofence = data.reduce((acc, event) => {
    const key = event.geofence_name
    if (!acc[key]) acc[key] = []
    acc[key].push(event)
    return acc
  }, {} as Record<string, GeofenceEvent[]>)

  // Calcular centro do mapa com base nos eventos
  const centerLat = data.reduce((sum, e) => sum + e.latitude, 0) / data.length
  const centerLng = data.reduce((sum, e) => sum + e.longitude, 0) / data.length

  return (
    <div>
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
        <p className="text-sm text-blue-700">
          <strong>📍 Eventos de Geofence</strong> – {data.length} evento(s) registrado(s) no período.
          {stops && stops.length > 0 && ` • ${stops.length} parada(s) identificada(s).`}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Mapa */}
        <div className="lg:col-span-2 h-96 rounded-lg overflow-hidden border">
          <MapContainer
            center={[centerLat || -23.515, centerLng || -46.865]}
            zoom={14}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; OpenStreetMap contributors'
            />

            {/* Eventos de Geofence (entrada/saída) */}
            {data.map((event, index) => {
              const icon = event.event_type === 'enter' ? enterIcon : exitIcon
              const label = event.event_type === 'enter' ? 'Entrada' : 'Saída'
              return (
                <Marker
                  key={`${event.geofence_name}-${index}`}
                  position={[event.latitude, event.longitude]}
                  icon={icon}
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
                icon={stopIcon}
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
                  <div key={idx} className="flex items-center gap-2 text-xs text-gray-600 mt-1">
                    {event.event_type === 'enter' ? (
                      <ArrowRight className="w-3 h-3 text-green-600" />
                    ) : (
                      <ArrowLeft className="w-3 h-3 text-orange-600" />
                    )}
                    <span>{event.event_type === 'enter' ? 'Entrada' : 'Saída'}</span>
                    <span>•</span>
                    <span>{formatTime(event.timestamp)}</span>
                  </div>
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
                  <div key={index} className="flex items-center justify-between p-2 border rounded-lg hover:bg-gray-50">
                    <div>
                      <p className="text-sm font-medium">Parada {index + 1}</p>
                      <p className="text-xs text-gray-500">
                        {formatTime(stop.start_time)} - {formatTime(stop.end_time)}
                      </p>
                    </div>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                      {formatDuration(stop.duration_minutes)}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}