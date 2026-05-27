// frontend/src/pages/TechniciansPage.tsx
import { useEffect, useState } from 'react'
import { Trash2, Plus, Edit2, MapPin } from 'lucide-react'
import Layout from '@/components/Layout'
import api from '@/services/api'
import { Technician } from '@/types'
import toast from 'react-hot-toast'
import LoadingSpinner from '@/components/LoadingSpinner'

interface FormData {
  name: string
  employee_id: string
  email: string
  phone: string
  cpf?: string | null
  notes: string
}

const initialFormData: FormData = {
  name: '',
  employee_id: '',
  email: '',
  phone: '',
  cpf: null,
  notes: '',
}

export default function TechniciansPage() {
  const [technicians, setTechnicians] = useState<Technician[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState<FormData>(initialFormData)
  const [filterOnline, setFilterOnline] = useState<boolean | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    fetchTechnicians()
  }, [])

  const fetchTechnicians = async () => {
    try {
      setIsLoading(true)
      const data = await api.getTechnicians(filterOnline ?? undefined)
      setTechnicians(data)
    } catch (error) {
      toast.error('Erro ao carregar técnicos')
      console.error(error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (isSubmitting) return

    setIsSubmitting(true)
    try {
    const submitData = {
         name: formData.name,
         employee_id: formData.employee_id,
         ...(formData.email && { email: formData.email }),
         ...(formData.phone && { phone: formData.phone }),
         ...(formData.cpf && { cpf: formData.cpf }),
         ...(formData.notes && { notes: formData.notes })
       }

      if (editingId) {
        await api.updateTechnician(editingId, submitData)
        toast.success('Técnico atualizado com sucesso!')
      } else {
        await api.createTechnician(submitData)
        toast.success('Técnico criado com sucesso!')
      }

      setShowModal(false)
      setEditingId(null)
      setFormData(initialFormData)
      fetchTechnicians()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar técnico')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEdit = (technician: Technician) => {
    setFormData({
      name: technician.name,
      employee_id: technician.employee_id,
      email: technician.email || '',
      phone: technician.phone || '',
      cpf: technician.cpf || null,
      notes: technician.notes || '',
    })
    setEditingId(technician.id)
    setShowModal(true)
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('Tem certeza que deseja deletar este técnico?')) {
      return
    }

    try {
      await api.deleteTechnician(id)
      toast.success('Técnico deletado com sucesso!')
      fetchTechnicians()
    } catch (error) {
      toast.error('Erro ao deletar técnico')
    }
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setEditingId(null)
    setFormData(initialFormData)
  }

  const filteredTechnicians =
    filterOnline === null
      ? technicians
      : technicians.filter((t) => t.is_online === filterOnline)

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Técnicos</h1>
            <p className="text-gray-600">Gerenciamento de técnicos corporativos</p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-1 md:gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-1.5 md:py-2 px-3 md:px-4 rounded-lg transition text-sm md:text-base"
          >
            <Plus size={16} className="md:w-5 md:h-5" />
            <span className="hidden sm:inline">Novo Técnico</span>
            <span className="sm:hidden">Novo</span>
          </button>
        </div>

        {/* Filtros */}
        <div className="bg-white rounded-lg shadow p-4 flex gap-4">
          <button
            onClick={() => {
              setFilterOnline(null)
              fetchTechnicians()
            }}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              filterOnline === null
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Todos
          </button>
          <button
            onClick={() => setFilterOnline(true)}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              filterOnline === true
                ? 'bg-green-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Online
          </button>
          <button
            onClick={() => setFilterOnline(false)}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              filterOnline === false
                ? 'bg-red-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Offline
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-4">
          <div className="bg-white rounded-lg shadow p-3 md:p-4">
            <p className="text-gray-600 text-xs md:text-sm">Total de Técnicos</p>
            <p className="text-2xl md:text-3xl font-bold text-gray-900 mt-1 md:mt-2">
              {technicians.length}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Online Agora</p>
            <p className="text-3xl font-bold text-green-600 mt-2">
              {technicians.filter((t) => t.is_online).length}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Offline</p>
            <p className="text-3xl font-bold text-red-600 mt-2">
              {technicians.filter((t) => !t.is_online).length}
            </p>
          </div>
        </div>

        {/* Tabela */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {isLoading ? (
            <div className="p-8 text-center">
              <LoadingSpinner size="md" message="Carregando técnicos..." />
            </div>
          ) : filteredTechnicians.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-gray-600">Nenhum técnico encontrado</p>
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
                      ID Func.
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                      Telefone
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                      Bateria
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filteredTechnicians.map((technician) => (
                    <tr key={technician.id} className="hover:bg-gray-50 transition">
                      <td className="px-6 py-4">
                        <div>
                          <p className="font-medium text-gray-900">
                            {technician.name}
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-gray-600">{technician.employee_id}</p>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-gray-600">{technician.email || '-'}</p>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-gray-600">{technician.phone || '-'}</p>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
                            technician.is_online
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          <span
                            className={`w-2 h-2 rounded-full ${
                              technician.is_online ? 'bg-green-600' : 'bg-red-600'
                            }`}
                          ></span>
                          {technician.is_online ? 'Online' : 'Offline'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className={`h-full transition-all ${
                                (technician.battery_level || 0) > 50
                                  ? 'bg-green-500'
                                  : (technician.battery_level || 0) > 20
                                    ? 'bg-yellow-500'
                                    : 'bg-red-500'
                              }`}
                              style={{
                                width: `${technician.battery_level || 0}%`,
                              }}
                            ></div>
                          </div>
                          <span className="text-sm text-gray-600">
                            {technician.battery_level || 0}%
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleEdit(technician)}
                            className="p-2 hover:bg-blue-50 text-blue-600 rounded-lg transition"
                            title="Editar"
                          >
                            <Edit2 size={18} />
                          </button>
                          <button
                            onClick={() => {
                              if (technician.latitude && technician.longitude) {
                                window.open(
                                  `https://maps.google.com/?q=${technician.latitude},${technician.longitude}`,
                                  '_blank'
                                )
                              }
                            }}
                            disabled={!technician.latitude}
                            className="p-2 hover:bg-green-50 text-green-600 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Ver localização"
                          >
                            <MapPin size={18} />
                          </button>
                          <button
                            onClick={() => handleDelete(technician.id)}
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
              {editingId ? 'Editar Técnico' : 'Novo Técnico'}
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
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ID Funcionário *
                </label>
                <input
                  type="text"
                  name="employee_id"
                  value={formData.employee_id}
                  onChange={handleChange}
                  required
                  disabled={!!editingId}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Telefone
                </label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  CPF
                </label>
                <input
                  type="text"
                  name="cpf"
                  value={formData.cpf || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notas
                </label>
                <textarea
                  name="notes"
                  value={formData.notes}
                  onChange={handleChange}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                ></textarea>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition"
                >
                  {isSubmitting ? 'Salvando...' : (editingId ? 'Atualizar' : 'Criar')}
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
          </div>
        </div>
      )}
    </Layout>
  )
}