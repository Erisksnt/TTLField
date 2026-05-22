import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Circle, Polygon, useMap } from 'react-leaflet'
import { LatLngTuple } from 'leaflet'
import { Trash2, Plus, Edit2, Map as MapIcon } from 'lucide-react'
import Layout from '@/components/Layout'
import api from '@/services/api'
import { Geofence } from '@/types'
import toast from 'react-hot-toast'

type GeofenceTypeOption = 'circle' | 'polygon' | 'rectangle'

interface FormData {
  name: string
  description: string
  geofence_type: GeofenceTypeOption
  radius_meters?: number
  coordinates?: Array<[number, number]>
  alert_on_enter: boolean
  alert_on_exit: boolean
}

const initialFormData: FormData = {
  name: '',
  description: '',
  geofence_type: 'circle',
  radius_meters: 500,
  coordinates: [],
  alert_on_enter: true,
  alert_on_exit: true,
}

function MapController() {
  const map = useMap()
  useEffect(() => {
    map.setView([-23.55, -46.63], 11)
  }, [map])
  return null
}

export default function GeofencesPage() {
  const [geofences, setGeofences] = useState<Geofence[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState<FormData>(initialFormData)
  const [selectedGeofence, setSelectedGeofence] = useState<string | null>(null)

  useEffect(() => {
    fetchGeofences()
  }, [])

  const fetchGeofences = async () => {
    try {
      setIsLoading(true)
      const data = await api.getGeofences()
      setGeofences(data)
    } catch (error) {
      toast.error('Erro ao carregar geofences')
      console.error(error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value, type } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]:
        type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    try {
      const geometry =
        formData.geofence_type === 'circle'
          ? {
              type: 'Point',
              coordinates: [-46.63, -23.55], // Esse será substituído pelo usuário
            }
          : {
              type: 'Polygon',
              coordinates: formData.coordinates || [],
            }

      const payload = {
        ...formData,
        geometry,
      }

      if (editingId) {
        await api.updateGeofence(editingId, payload)
        toast.success('Geofence atualizado com sucesso!')
      } else {
        await api.createGeofence(payload)
        toast.success('Geofence criado com sucesso!')
      }

      setShowModal(false)
      setEditingId(null)
      setFormData(initialFormData)
      fetchGeofences()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar geofence')
    }
  }

  const handleEdit = (geofence: Geofence) => {
    setFormData({
      name: geofence.name,
      description: geofence.description || '',
      geofence_type: geofence.geofence_type,
      alert_on_enter: geofence.alert_on_enter,
      alert_on_exit: geofence.alert_on_exit,
    })
    setEditingId(geofence.id)
    setShowModal(true)
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('Tem certeza que deseja deletar este geofence?')) {
      return
    }

    try {
      await api.deleteGeofence(id)
      toast.success('Geofence deletado com sucesso!')
      fetchGeofences()
    } catch (error) {
      toast.error('Erro ao deletar geofence')
    }
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setEditingId(null)
    setFormData(initialFormData)
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Geofences</h1>
            <p className="text-gray-600">Gerenciamento de cercas geográficas</p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-1 md:gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-1.5 md:py-2 px-3 md:px-4 rounded-lg transition text-sm md:text-base"
          >
            <Plus size={16} className="md:w-5 md:h-5" />
            <span className="hidden sm:inline">Novo Geofence</span>
            <span className="sm:hidden">Novo</span>
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Total de Geofences</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {geofences.length}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Ativos</p>
            <p className="text-3xl font-bold text-green-600 mt-2">
              {geofences.filter((g) => g.is_active).length}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Inativos</p>
            <p className="text-3xl font-bold text-red-600 mt-2">
              {geofences.filter((g) => !g.is_active).length}
            </p>
          </div>
        </div>

        {/* Mapa */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Mapa de Geofences</h2>
          <div className="h-96 rounded-lg overflow-hidden border">
            <MapContainer
              center={[-23.55, -46.63] as LatLngTuple}
              zoom={11}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; OpenStreetMap contributors'
              />
              <MapController />

              {geofences.map((geofence) => {
                if (geofence.geofence_type === 'circle') {
                  return (
                    <Circle
                      key={geofence.id}
                      center={[-23.55, -46.63]}
                      radius={500}
                      pathOptions={{
                        color: geofence.is_active ? '#3b82f6' : '#999',
                        fillOpacity: 0.2,
                      }}
                    />
                  )
                }
                return null
              })}
            </MapContainer>
          </div>
        </div>

        {/* Tabela */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {isLoading ? (
            <div className="p-8 text-center">
              <p className="text-gray-600">Carregando geofences...</p>
            </div>
          ) : geofences.length === 0 ? (
            <div className="p-8 text-center">
              <MapIcon size={48} className="mx-auto text-gray-400 mb-3" />
              <p className="text-gray-600">Nenhum geofence criado</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                      Nome
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                      Descrição
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                      Alertas
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {geofences.map((geofence) => (
                    <tr
                      key={geofence.id}
                      className="hover:bg-gray-50 transition cursor-pointer"
                      onClick={() => setSelectedGeofence(geofence.id)}
                    >
                      <td className="px-6 py-4">
                        <p className="font-medium text-gray-900">
                          {geofence.name}
                        </p>
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                          {geofence.geofence_type === 'circle'
                            ? '◯ Círculo'
                            : geofence.geofence_type === 'polygon'
                              ? '▢ Polígono'
                              : '▭ Retângulo'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-gray-600 text-sm">
                          {geofence.description || '-'}
                        </p>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
                            geofence.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          <span
                            className={`w-2 h-2 rounded-full ${
                              geofence.is_active ? 'bg-green-600' : 'bg-red-600'
                            }`}
                          ></span>
                          {geofence.is_active ? 'Ativo' : 'Inativo'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex gap-2">
                          <span
                            className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                              geofence.alert_on_enter
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            Entrada
                          </span>
                          <span
                            className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                              geofence.alert_on_exit
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            Saída
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleEdit(geofence)
                            }}
                            className="p-2 hover:bg-blue-50 text-blue-600 rounded-lg transition"
                            title="Editar"
                          >
                            <Edit2 size={18} />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDelete(geofence.id)
                            }}
                            className="p-2 hover:bg-red-50 text-red-600 rounded-lg transition"
                            title="Deletar"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              {editingId ? 'Editar Geofence' : 'Novo Geofence'}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome *
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                  placeholder="Ex: Escritório Principal"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descrição
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                  placeholder="Descrição do geofence"
                ></textarea>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Geofence *
                </label>
                <select
                  name="geofence_type"
                  value={formData.geofence_type}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                >
                  <option value="circle">Círculo</option>
                  <option value="polygon">Polígono</option>
                  <option value="rectangle">Retângulo</option>
                </select>
              </div>

              {formData.geofence_type === 'circle' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Raio (metros)
                  </label>
                  <input
                    type="number"
                    name="radius_meters"
                    value={formData.radius_meters}
                    onChange={handleChange}
                    min="10"
                    max="10000"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                  />
                </div>
              )}

              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-700">Alertas</p>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="alert_enter"
                    name="alert_on_enter"
                    checked={formData.alert_on_enter}
                    onChange={handleChange}
                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
                  />
                  <label htmlFor="alert_enter" className="text-sm text-gray-700">
                    Alerta ao entrar no geofence
                  </label>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="alert_exit"
                    name="alert_on_exit"
                    checked={formData.alert_on_exit}
                    onChange={handleChange}
                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
                  />
                  <label htmlFor="alert_exit" className="text-sm text-gray-700">
                    Alerta ao sair do geofence
                  </label>
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition"
                >
                  {editingId ? 'Atualizar' : 'Criar'}
                </button>
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-900 font-semibold py-2 px-4 rounded-lg transition"
                >
                  Cancelar
                </button>
              </div>
            </form>

            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-xs text-blue-700">
                <strong>💡 Dica:</strong> Você pode desenhar geofences no mapa
                acima após criar a cerca.
              </p>
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}
