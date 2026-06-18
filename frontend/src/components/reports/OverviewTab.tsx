// frontend/src/components/reports/OverviewTab.tsx
import { TrendingUp, Clock, MapPin, AlertTriangle } from 'lucide-react'

interface SummaryData {
  total_distance_km: number
  total_time_minutes: number
  average_speed_kmh: number
  max_speed_kmh: number
  total_stops: number
  geofence_events_count: number
  alerts_count: number
}

interface OverviewTabProps {
  data?: SummaryData
}

// Função para formatar minutos em "Xh Ymin"
const formatTime = (minutes: number): string => {
  if (!minutes || minutes < 0) return '0min'
  const hours = Math.floor(minutes / 60)
  const mins = Math.round(minutes % 60)
  if (hours === 0) return `${mins}min`
  if (mins === 0) return `${hours}h`
  return `${hours}h ${mins}min`
}

export default function OverviewTab({ data }: OverviewTabProps) {
  if (!data) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p className="text-lg">📊 Nenhum dado disponível para o período selecionado</p>
      </div>
    )
  }

  const stats = [
    {
      label: 'Distância Total',
      value: `${data.total_distance_km.toFixed(1)} km`,
      icon: TrendingUp,
      color: 'blue',
    },
    {
      label: 'Tempo em Viagem',
      value: formatTime(data.total_time_minutes),
      icon: Clock,
      color: 'green',
    },
    {
      label: 'Velocidade Média',
      value: `${data.average_speed_kmh.toFixed(1)} km/h`,
      icon: MapPin,
      color: 'yellow',
    },
    {
      label: 'Alertas',
      value: String(data.alerts_count),
      icon: AlertTriangle,
      color: 'red',
    },
  ]

  // Cards adicionais (stops e geofence events) 
  const extraStats = [
    { label: 'Paradas', value: data.total_stops, color: 'purple' },
    { label: 'Eventos de Geofence', value: data.geofence_events_count, color: 'indigo' },
  ]

  return (
    <div className="space-y-4">
      {/* Cards principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          const borderColor = {
            blue: 'border-blue-500',
            green: 'border-green-500',
            yellow: 'border-yellow-500',
            red: 'border-red-500',
          }[stat.color]

          return (
            <div key={stat.label} className={`bg-white rounded-lg shadow p-4 border-l-4 ${borderColor}`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">{stat.label}</p>
                  <p className="text-2xl font-bold">{stat.value}</p>
                </div>
                <Icon className={`w-8 h-8 text-${stat.color}-500`} />
              </div>
            </div>
          )
        })}
      </div>

      {/* Cards extras (paradas e geofences) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {extraStats.map((stat) => {
          const borderColor = {
            purple: 'border-purple-500',
            indigo: 'border-indigo-500',
          }[stat.color]

          return (
            <div key={stat.label} className={`bg-white rounded-lg shadow p-4 border-l-4 ${borderColor}`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">{stat.label}</p>
                  <p className="text-2xl font-bold">{stat.value}</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}