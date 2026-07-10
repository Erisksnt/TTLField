// frontend/src/pages/ReportsPage.tsx
import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import Layout from '@/components/Layout'
import OverviewTab from '@/components/reports/OverviewTab'
import RouteTab from '@/components/reports/RouteTab'
import GeofenceTab from '@/components/reports/GeofenceTab'
import AlertsTab from '@/components/reports/AlertsTab'
import api from '@/services/api'
import { Technician } from '@/types'
import toast from 'react-hot-toast'

type TabType = 'overview' | 'route' | 'geofence' | 'alerts'
type DatePeriod = 'today' | 'yesterday' | 'this_week' | 'previous_week' | 'this_month' | 'previous_month' | 'custom'

const tabs: { id: TabType; label: string; icon: string }[] = [
  { id: 'overview', label: 'Visão Geral', icon: '📊' },
  { id: 'route', label: 'Rota', icon: '🗺️' },
  { id: 'geofence', label: 'Geofences & Paradas', icon: '📍' },
  { id: 'alerts', label: 'Alertas', icon: '🔔' },
]

const periodOptions: { value: DatePeriod; label: string }[] = [
  { value: 'today', label: 'Hoje' },
  { value: 'yesterday', label: 'Ontem' },
  { value: 'this_week', label: 'Esta Semana' },
  { value: 'previous_week', label: 'Semana Anterior' },
  { value: 'this_month', label: 'Este Mês' },
  { value: 'previous_month', label: 'Mês Anterior' },
  { value: 'custom', label: 'Personalizado' },
]

const formatDateInput = (date: Date) => {
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

const getDateRangeForPeriod = (period: DatePeriod) => {
  const today = new Date()
  const start = new Date(today)
  const end = new Date(today)

  if (period === 'custom') {
    return { startDate: formatDateInput(today), endDate: formatDateInput(today) }
  }

  if (period === 'yesterday') {
    start.setDate(today.getDate() - 1)
    end.setDate(today.getDate() - 1)
    start.setHours(0, 0, 0, 0)
    end.setHours(23, 59, 59, 999)
    return { startDate: formatDateInput(start), endDate: formatDateInput(end) }
  }

  if (period === 'this_week') {
    const day = today.getDay()
    const diff = day === 0 ? -6 : 1 - day
    start.setDate(today.getDate() + diff)
    start.setHours(0, 0, 0, 0)
    end.setHours(23, 59, 59, 999)
    return { startDate: formatDateInput(start), endDate: formatDateInput(end) }
  }

  if (period === 'previous_week') {
    const day = today.getDay()
    const diff = day === 0 ? -13 : 1 - day - 7
    start.setDate(today.getDate() + diff)
    end.setDate(start.getDate() + 6)
    start.setHours(0, 0, 0, 0)
    end.setHours(23, 59, 59, 999)
    return { startDate: formatDateInput(start), endDate: formatDateInput(end) }
  }

  if (period === 'this_month') {
    start.setDate(1)
    start.setHours(0, 0, 0, 0)
    end.setHours(23, 59, 59, 999)
    return { startDate: formatDateInput(start), endDate: formatDateInput(end) }
  }

  if (period === 'previous_month') {
    const firstDayOfCurrentMonth = new Date(today.getFullYear(), today.getMonth(), 1)
    start.setTime(firstDayOfCurrentMonth.getTime())
    start.setMonth(start.getMonth() - 1)
    start.setDate(1)
    start.setHours(0, 0, 0, 0)

    end.setTime(firstDayOfCurrentMonth.getTime())
    end.setDate(0)
    end.setHours(23, 59, 59, 999)
    return { startDate: formatDateInput(start), endDate: formatDateInput(end) }
  }

  start.setHours(0, 0, 0, 0)
  end.setHours(23, 59, 59, 999)
  return { startDate: formatDateInput(start), endDate: formatDateInput(end) }
}

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [technicians, setTechnicians] = useState<Technician[]>([])
  const [selectedTechnician, setSelectedTechnician] = useState<string>('')
  const [selectedPeriod, setSelectedPeriod] = useState<DatePeriod>('today')
  const [startDate, setStartDate] = useState<string>(() => getDateRangeForPeriod('today').startDate)
  const [endDate, setEndDate] = useState<string>(() => getDateRangeForPeriod('today').endDate)
  const [isLoading, setIsLoading] = useState(false)
  const [reportData, setReportData] = useState<any>(null)
  const location = useLocation()

  // Carregar lista de técnicos
  useEffect(() => {
    const fetchTechnicians = async () => {
      try {
        const data = await api.getTechnicians(undefined, 0, 1000)
        setTechnicians(data)
        try {
          const params = new URLSearchParams(location.search)
          const paramTech = params.get('technicianId')
          if (paramTech && data.find((t) => t.id === paramTech)) {
            setSelectedTechnician(paramTech)
          } else if (data.length > 0) {
            setSelectedTechnician(data[0].id)
          }
        } catch (e) {
          if (data.length > 0) setSelectedTechnician(data[0].id)
        }
      } catch (error) {
        toast.error('Erro ao carregar técnicos')
        console.error(error)
      }
    }
    fetchTechnicians()
  }, [location.search])

  const handlePeriodChange = (period: DatePeriod) => {
    setSelectedPeriod(period)

    if (period === 'custom') {
      return
    }

    const { startDate: nextStartDate, endDate: nextEndDate } = getDateRangeForPeriod(period)
    setStartDate(nextStartDate)
    setEndDate(nextEndDate)
  }

  // Buscar dados do relatório
  const fetchReportData = async () => {
    if (!selectedTechnician) {
      toast.error('Selecione um técnico')
      return
    }

    if (!startDate || !endDate) {
      toast.error('Selecione as datas')
      return
    }

    setIsLoading(true)
    try {
      // Converter datas para formato ISO com hora (meia-noite)
      const start = `${startDate}T00:00:00`
      const end = `${endDate}T23:59:59`

      const [summary, route, geofenceEvents, stops, alerts] = await Promise.all([
        api.getReportSummary(selectedTechnician, start, end),
        api.getRoute(selectedTechnician, start, end),
        api.getGeofenceEvents(selectedTechnician, start, end),
        api.getStops(selectedTechnician, start, end),
        api.getAlertsReport(selectedTechnician, start, end),
      ])

      setReportData({
        summary,
        route,
        geofenceEvents,
        stops,
        alerts,
      })
      toast.success('Relatório atualizado!')
    } catch (error) {
      console.error('Erro ao buscar relatório:', error)
      toast.error('Erro ao carregar dados do relatório')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (selectedTechnician && startDate && endDate) {
      fetchReportData()
    }
  }, [selectedTechnician, startDate, endDate])

  return (
    <Layout>
      <div className="space-y-6">
        {/* Cabeçalho */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Relatórios</h1>
            <p className="text-gray-600">Análise detalhada da operação</p>
          </div>
        </div>

        {/* Filtros */}
        <div className="bg-white rounded-lg shadow p-4 flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-[180px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">Técnico</label>
            <select 
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              value={selectedTechnician}
              onChange={(e) => setSelectedTechnician(e.target.value)}
            >
              {technicians.map((tech) => (
                <option key={tech.id} value={tech.id}>
                  {tech.name} ({tech.employee_id})
                </option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-w-[220px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">Período</label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              value={selectedPeriod}
              onChange={(e) => handlePeriodChange(e.target.value as DatePeriod)}
            >
              {periodOptions.map((period) => (
                <option key={period.value} value={period.value}>
                  {period.label}
                </option>
              ))}
            </select>
          </div>
          {selectedPeriod === 'custom' && (
            <>
              <div className="flex-1 min-w-[150px]">
                <label className="block text-sm font-medium text-gray-700 mb-1">Data Início</label>
                <input
                  type="date"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>
              <div className="flex-1 min-w-[150px]">
                <label className="block text-sm font-medium text-gray-700 mb-1">Data Fim</label>
                <input
                  type="date"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>
            </>
          )}
          <div className="flex items-end">
            <button 
              onClick={fetchReportData}
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition disabled:opacity-50"
            >
              {isLoading ? 'Carregando...' : 'Aplicar Filtros'}
            </button>
          </div>
        </div>

        {/* Abas */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200">
            <nav className="flex flex-wrap gap-1 p-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-2 rounded-lg font-medium transition ${
                    activeTab === tab.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-4">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-3 text-gray-600">Carregando dados...</span>
              </div>
            ) : reportData ? (
              <>
                {activeTab === 'overview' && <OverviewTab data={reportData.summary} />}
                {activeTab === 'route' && <RouteTab data={reportData.route} />}
                {activeTab === 'geofence' && <GeofenceTab data={reportData.geofenceEvents} stops={reportData.stops} />}
                {activeTab === 'alerts' && <AlertsTab data={reportData.alerts} />}
              </>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <p>Selecione um técnico e um período para carregar os dados.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}