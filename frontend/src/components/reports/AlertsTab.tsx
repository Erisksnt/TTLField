// frontend/src/components/reports/AlertsTab.tsx
import { AlertTriangle, CheckCircle, Clock } from 'lucide-react'

interface AlertItem {
  id: string
  alert_type: string
  description: string | null
  severity: string
  triggered_at: string
  is_acknowledged: boolean
}

interface AlertsTabProps {
  data?: AlertItem[]
}

export default function AlertsTab({ data }: AlertsTabProps) {
  // Se não houver dados, exibe mensagem
  if (!data || data.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p className="text-lg">🔔 Nenhum alerta encontrado para o período selecionado</p>
      </div>
    )
  }

  // Função para formatar a data/hora
  const formatTime = (isoString: string) => {
    const date = new Date(isoString)
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // Mapeamento de severidade para cores
  const severityColors: Record<string, string> = {
    critical: 'bg-red-100 text-red-800',
    high: 'bg-orange-100 text-orange-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-blue-100 text-blue-800',
  }

  return (
    <div>
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
        <p className="text-sm text-blue-700">
          <strong>📋 Histórico de alertas e eventos</strong> – {data.length} alerta(s) encontrado(s) no período selecionado.
        </p>
      </div>

      <div className="bg-white rounded-lg border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Tipo</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Descrição</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Severidade</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Data/Hora</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {data.map((alert) => (
                <tr key={alert.id} className="hover:bg-gray-50 transition">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-yellow-500" />
                      <span className="text-sm font-medium">{alert.alert_type}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {alert.description || '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      severityColors[alert.severity.toLowerCase()] || 'bg-gray-100 text-gray-600'
                    }`}>
                      {alert.severity}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatTime(alert.triggered_at)}
                  </td>
                  <td className="px-4 py-3">
                    {alert.is_acknowledged ? (
                      <span className="flex items-center gap-1 text-xs text-green-600">
                        <CheckCircle className="w-3 h-3" /> Reconhecido
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-red-600">
                        <AlertTriangle className="w-3 h-3" /> Pendente
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}