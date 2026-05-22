import { useEffect, useState } from 'react'
import { Bell, Check, X, AlertTriangle } from 'lucide-react'
import Layout from '@/components/Layout'
import api from '@/services/api'
import { Alert, Technician } from '@/types'
import toast from 'react-hot-toast'
import { formatDistanceToNow } from 'date-fns'
import { ptBR } from 'date-fns/locale'

type AlertSeverity = 'low' | 'medium' | 'high' | 'critical'
type AlertType = 'all' | 'active' | 'acknowledged'

const severityColors: Record<AlertSeverity, { bg: string; text: string; border: string }> = {
  low: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  medium: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  high: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
  critical: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
}

const alertTypeDescriptions: Record<string, string> = {
  speeding: 'Excesso de velocidade',
  offline: 'Dispositivo offline',
  geofence_exit: 'Saída de geofence',
  geofence_enter: 'Entrada de geofence',
  low_battery: 'Bateria baixa',
  stationary: 'Sem movimentação',
  movement_detected: 'Movimento detectado',
  device_offline: 'Dispositivo desconectado',
  heart_beat_missed: 'Heartbeat perdido',
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [technicians, setTechnicians] = useState<Record<string, Technician>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [filterType, setFilterType] = useState<AlertType>('active')
  const [filterSeverity, setFilterSeverity] = useState<AlertSeverity | 'all'>('all')
  const [expandedAlert, setExpandedAlert] = useState<string | null>(null)

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 15000) // Atualizar a cada 15s
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      setIsLoading(true)
      const [alertsData, techniciansData] = await Promise.all([
        api.getAlerts(),
        api.getTechnicians(undefined, 0, 1000),
      ])

      setAlerts(alertsData)

      // Criar mapa de técnicos para acesso rápido
      const techMap: Record<string, Technician> = {}
      techniciansData.forEach((tech) => {
        techMap[tech.id] = tech
      })
      setTechnicians(techMap)
    } catch (error) {
      toast.error('Erro ao carregar alertas')
      console.error(error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAcknowledge = async (alertId: string) => {
    try {
      await api.acknowledgeAlert(alertId, 'Administrator')
      toast.success('Alerta reconhecido')
      fetchData()
    } catch (error) {
      toast.error('Erro ao reconhecer alerta')
    }
  }

  const filteredAlerts = alerts.filter((alert) => {
    // Filtro por tipo
    if (filterType === 'active' && !alert.is_active) return false
    if (filterType === 'acknowledged' && !alert.is_acknowledged) return false

    // Filtro por severidade
    if (filterSeverity !== 'all' && alert.severity !== filterSeverity) return false

    return true
  })

  const statsAlerts = {
    total: alerts.length,
    active: alerts.filter((a) => a.is_active).length,
    critical: alerts.filter((a) => a.severity === 'critical').length,
    acknowledged: alerts.filter((a) => a.is_acknowledged).length,
  }

  const severityDistribution = {
    critical: alerts.filter((a) => a.severity === 'critical').length,
    high: alerts.filter((a) => a.severity === 'high').length,
    medium: alerts.filter((a) => a.severity === 'medium').length,
    low: alerts.filter((a) => a.severity === 'low').length,
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Alertas</h1>
            <p className="text-gray-600">Monitoramento de alertas operacionais</p>
          </div>
          {statsAlerts.critical > 0 && (
            <div className="bg-red-100 border border-red-300 rounded-lg px-4 py-2">
              <p className="text-red-800 font-semibold">
                ⚠️ {statsAlerts.critical} alerta(s) crítico(s)
              </p>
            </div>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Total de Alertas</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {statsAlerts.total}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Alertas Ativos</p>
            <p className="text-3xl font-bold text-red-600 mt-2">
              {statsAlerts.active}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Críticos</p>
            <p className="text-3xl font-bold text-red-700 mt-2">
              {statsAlerts.critical}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Reconhecidos</p>
            <p className="text-3xl font-bold text-green-600 mt-2">
              {statsAlerts.acknowledged}
            </p>
          </div>
        </div>

        {/* Distribuição de severidade */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">
            Distribuição por Severidade
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-red-600 rounded-full"></div>
              <div>
                <p className="text-sm text-gray-600">Críticos</p>
                <p className="text-2xl font-bold text-red-600">
                  {severityDistribution.critical}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-orange-600 rounded-full"></div>
              <div>
                <p className="text-sm text-gray-600">Altos</p>
                <p className="text-2xl font-bold text-orange-600">
                  {severityDistribution.high}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-yellow-600 rounded-full"></div>
              <div>
                <p className="text-sm text-gray-600">Médios</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {severityDistribution.medium}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-blue-600 rounded-full"></div>
              <div>
                <p className="text-sm text-gray-600">Baixos</p>
                <p className="text-2xl font-bold text-blue-600">
                  {severityDistribution.low}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Filtros */}
        <div className="bg-white rounded-lg shadow p-4 space-y-4">
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-700">Status</p>
            <div className="flex gap-2">
              {(['active', 'acknowledged', 'all'] as const).map((type) => (
                <button
                  onClick={() => setFilterType(type)}
                  className={`px-2 md:px-4 py-1 md:py-2 rounded-lg font-medium transition text-sm md:text-base ${
                    filterType === type
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {type === 'active' ? 'Ativos' : type === 'acknowledged' ? 'Reconhecidos' : 'Todos'}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-700">Severidade</p>
            <div className="flex gap-2 flex-wrap">
              {(['all', 'critical', 'high', 'medium', 'low'] as const).map(
                (severity) => (
                  <button
                    key={severity}
                    onClick={() => setFilterSeverity(severity as any)}
                    className={`px-4 py-2 rounded-lg font-medium transition ${
                      filterSeverity === severity
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    {severity === 'all'
                      ? 'Todas'
                      : severity === 'critical'
                        ? 'Crítica'
                        : severity === 'high'
                          ? 'Alta'
                          : severity === 'medium'
                            ? 'Média'
                            : 'Baixa'}
                  </button>
                )
              )}
            </div>
          </div>
        </div>

        {/* Lista de alertas */}
        <div className="space-y-3">
          {isLoading ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <p className="text-gray-600">Carregando alertas...</p>
            </div>
          ) : filteredAlerts.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <Bell size={48} className="mx-auto text-gray-400 mb-3" />
              <p className="text-gray-600">Nenhum alerta encontrado</p>
            </div>
          ) : (
            filteredAlerts.map((alert) => {
              const colors = severityColors[alert.severity]
              const technician = technicians[alert.technician_id]
              const isExpanded = expandedAlert === alert.id

              return (
                <div
                  key={alert.id}
                  className={`border rounded-lg overflow-hidden transition cursor-pointer ${colors.border} ${colors.bg}`}
                >
                  <button
                    onClick={() =>
                      setExpandedAlert(isExpanded ? null : alert.id)
                    }
                    className="w-full text-left p-4 hover:opacity-80 transition"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <AlertTriangle size={20} className={colors.text} />
                          <h3 className={`font-semibold text-lg ${colors.text}`}>
                            {alert.title}
                          </h3>
                          <span
                            className={`text-xs font-bold px-2 py-1 rounded ${
                              alert.severity === 'critical'
                                ? 'bg-red-600 text-white'
                                : alert.severity === 'high'
                                  ? 'bg-orange-600 text-white'
                                  : alert.severity === 'medium'
                                    ? 'bg-yellow-600 text-white'
                                    : 'bg-blue-600 text-white'
                            }`}
                          >
                            {alert.severity.toUpperCase()}
                          </span>
                        </div>

                        <div className="space-y-1 text-sm text-gray-700">
                          <p>
                            <strong>Tipo:</strong>{' '}
                            {alertTypeDescriptions[alert.alert_type] ||
                              alert.alert_type}
                          </p>
                          <p>
                            <strong>Técnico:</strong> {technician?.name || 'Desconhecido'}
                            {technician && ` (${technician.employee_id})`}
                          </p>
                          <p>
                            <strong>Disparado:</strong>{' '}
                            {formatDistanceToNow(
                              new Date(alert.triggered_at),
                              {
                                locale: ptBR,
                                addSuffix: true,
                              }
                            )}
                          </p>
                          {alert.description && (
                            <p>
                              <strong>Descrição:</strong> {alert.description}
                            </p>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2 ml-4">
                        {alert.is_acknowledged ? (
                          <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-600 text-white rounded-full text-sm font-medium">
                            <Check size={16} />
                            Reconhecido
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-3 py-1 bg-red-600 text-white rounded-full text-sm font-medium">
                            <AlertTriangle size={16} />
                            Ativo
                          </span>
                        )}
                      </div>
                    </div>

                    {isExpanded && alert.description && (
                      <div className="mt-4 pt-4 border-t border-gray-300">
                        <p className="text-sm text-gray-700 mb-3">
                          {alert.description}
                        </p>

                        {alert.metadata && (
                          <details className="text-xs text-gray-600 bg-white bg-opacity-50 p-2 rounded">
                            <summary className="cursor-pointer font-medium mb-2">
                              Dados Técnicos
                            </summary>
                            <pre className="overflow-auto">
                              {JSON.stringify(alert.metadata, null, 2)}
                            </pre>
                          </details>
                        )}

                        {!alert.is_acknowledged && (
                          <button
                            onClick={() => handleAcknowledge(alert.id)}
                            className="mt-3 w-full flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg transition"
                          >
                            <Check size={18} />
                            Reconhecer Alerta
                          </button>
                        )}
                      </div>
                    )}
                  </button>
                </div>
              )
            })
          )}
        </div>
      </div>
    </Layout>
  )
}
