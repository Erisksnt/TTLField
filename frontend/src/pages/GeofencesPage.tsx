// frontend/src/pages/GeofencesPage.tsx
import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Circle, Marker, Popup, useMap, Tooltip } from 'react-leaflet'
import { LatLngTuple, Icon } from 'leaflet'
import { Trash2, Plus, Edit2, Map as MapIcon, Target, Search } from 'lucide-react'
import Layout from '@/components/Layout'
import api from '@/services/api'
import { Geofence } from '@/types'
import toast from 'react-hot-toast'

interface FormData {
  name: string
  description: string
  radius: number
  alert_on_enter: boolean
  alert_on_exit: boolean
  center_latitude?: string
  center_longitude?: string
  address?: string
}

const initialFormData: FormData = {
  name: '',
  description: '',
  radius: 500,
  alert_on_enter: true,
  alert_on_exit: true,
  center_latitude: '',
  center_longitude: '',
  address: '',
}

// Função para buscar endereço a partir das coordenadas
const fetchAddress = async (lat: number, lng: number) => {
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

// Componente para controlar o mapa e permitir seleção
function MapSelector({ onLocationSelect, selectedLocation, isSelecting, onClose }: { 
  onLocationSelect: (lat: number, lng: number) => void
  selectedLocation: [number, number] | null
  isSelecting: boolean
  onClose: () => void
}) {
  const map = useMap()
  
  useEffect(() => {
    if (isSelecting) {
      map.getContainer().style.cursor = 'crosshair'
      
      const handleClick = (e: any) => {
        if (isSelecting) {
          onLocationSelect(e.latlng.lat, e.latlng.lng)
          onClose()
        }
      }
      
      map.on('click', handleClick)
      return () => {
        map.off('click', handleClick)
        map.getContainer().style.cursor = ''
      }
    }
  }, [map, isSelecting, onLocationSelect, onClose])
  
  useEffect(() => {
    if (selectedLocation) {
      map.setView(selectedLocation, 15)
    }
  }, [map, selectedLocation])
  
  return null
}

// Modal de seleção de localização
function LocationSelectorModal({ isOpen, onClose, onConfirm, initialLocation }: {
  isOpen: boolean
  onClose: () => void
  onConfirm: (lat: number, lng: number) => void
  initialLocation?: [number, number]
}) {
  const [tempLocation, setTempLocation] = useState<[number, number] | null>(initialLocation || null)
  const [searchAddress, setSearchAddress] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  
  if (!isOpen) return null
  
  const handleSearch = async () => {
    if (!searchAddress.trim()) return
    
    setIsSearching(true)
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchAddress)}&limit=1`
      )
      const data = await response.json()
      
      if (data && data.length > 0) {
        const lat = parseFloat(data[0].lat)
        const lon = parseFloat(data[0].lon)
        setTempLocation([lat, lon])
        toast.success('Localização encontrada!')
      } else {
        toast.error('Endereço não encontrado')
      }
    } catch (error) {
      toast.error('Erro ao buscar endereço')
    } finally {
      setIsSearching(false)
    }
  }
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-[10000]">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl p-6">
        <h3 className="text-xl font-bold mb-4">Selecionar Localização</h3>
        
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={searchAddress}
            onChange={(e) => setSearchAddress(e.target.value)}
            placeholder="Digite um endereço, cidade ou CEP..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button
            onClick={handleSearch}
            disabled={isSearching}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition flex items-center gap-2"
          >
            <Search size={18} />
            Buscar
          </button>
        </div>
        
        <div className="h-96 rounded-lg overflow-hidden border mb-4">
          <MapContainer
            center={tempLocation || [-23.55, -46.63]}
            zoom={tempLocation ? 15 : 11}
            style={{ height: '100%', width: '100%', zIndex: 1 }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; OpenStreetMap contributors'
            />
            <MapSelector 
              onLocationSelect={(lat, lng) => setTempLocation([lat, lng])}
              selectedLocation={tempLocation}
              isSelecting={true}
              onClose={() => {}}
            />
            {tempLocation && (
              <Marker position={tempLocation}>
                <Popup>Localização selecionada</Popup>
              </Marker>
            )}
          </MapContainer>
        </div>
        
        <p className="text-sm text-gray-600 mb-4 text-center">
          💡 Clique no mapa para selecionar a localização ou use a busca por endereço
        </p>
        
        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg transition"
          >
            Cancelar
          </button>
          <button
            onClick={() => tempLocation && onConfirm(tempLocation[0], tempLocation[1])}
            disabled={!tempLocation}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50"
          >
            Confirmar Localização
          </button>
        </div>
      </div>
    </div>
  )
}

export default function GeofencesPage() {
  const [geofences, setGeofences] = useState<Geofence[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [showLocationModal, setShowLocationModal] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState<FormData>(initialFormData)
  const [selectedGeofence, setSelectedGeofence] = useState<string | null>(null)
  const [selectedPosition, setSelectedPosition] = useState<[number, number] | null>(null)

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

  // Função - busca endereço e salva
  const handleConfirmLocation = async (lat: number, lng: number) => {
    setSelectedPosition([lat, lng])
    
    // Buscar endereço
    const address = await fetchAddress(lat, lng)
    
    setFormData(prev => ({
      ...prev,
      center_latitude: lat.toString(),
      center_longitude: lng.toString(),
      address: address,
    }))
    setShowLocationModal(false)
    toast.success('Localização definida!')
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

    if (!formData.center_latitude) {
      toast.error('Selecione a localização no mapa antes de criar o geofence')
      setShowLocationModal(true)
      return
    }

    if (!formData.radius) {
      toast.error('Defina o raio do círculo')
      return
    }

    try {
      const geometry = {
        type: 'Point',
        coordinates: [
          parseFloat(formData.center_longitude || '-46.63'),
          parseFloat(formData.center_latitude || '-23.55')
        ],
      }

      const payload = {
        name: formData.name,
        description: formData.description,
        geofence_type: 'circle' as const,
        radius: formData.radius,
        alert_on_enter: formData.alert_on_enter,
        alert_on_exit: formData.alert_on_exit,
        center_latitude: formData.center_latitude,
        center_longitude: formData.center_longitude,
        address: formData.address,
        geometry,
        is_active: true,
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
      setSelectedPosition(null)
      fetchGeofences()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar geofence')
    }
  }

  const handleEdit = (geofence: Geofence) => {
    setFormData({
      name: geofence.name,
      description: geofence.description || '',
      radius: geofence.radius || 500,
      alert_on_enter: geofence.alert_on_enter,
      alert_on_exit: geofence.alert_on_exit,
      center_latitude: geofence.center_latitude || '',
      center_longitude: geofence.center_longitude || '',
      address: geofence.address || '',
    })
    if (geofence.center_latitude && geofence.center_longitude) {
      setSelectedPosition([parseFloat(geofence.center_latitude), parseFloat(geofence.center_longitude)])
    }
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
    setSelectedPosition(null)
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
            <p className="text-3xl font-bold text-gray-900 mt-2">{geofences.length}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Ativos</p>
            <p className="text-3xl font-bold text-green-600 mt-2">{geofences.filter((g) => g.is_active).length}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Inativos</p>
            <p className="text-3xl font-bold text-red-600 mt-2">{geofences.filter((g) => !g.is_active).length}</p>
          </div>
        </div>

        {/* Mapa */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Mapa de Geofences</h2>
          <div className="h-96 rounded-lg overflow-hidden border">
            <MapContainer
              center={[-23.55, -46.63] as LatLngTuple}
              zoom={11}
              style={{ height: '100%', width: '100%', zIndex: 1 }}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; OpenStreetMap contributors'
              />
              
              {geofences.map((geofence) => {
                console.log('Renderizando geofence:', geofence.name, geofence.center_latitude, geofence.center_longitude)
                if (geofence.center_latitude && geofence.center_longitude) {
                  return (
                    <Circle
                      key={geofence.id}
                      center={[parseFloat(geofence.center_latitude), parseFloat(geofence.center_longitude)]}
                      radius={geofence.radius || 500}
                      pathOptions={{
                        color: geofence.is_active ? '#3b82f6' : '#999',
                        fillColor: geofence.is_active ? '#3b82f6' : '#999',
                        fillOpacity: 0.2,
                        weight: 2,
                      }}
                    >
                      <Tooltip sticky>
                        <div className="text-sm">
                          <p className="font-semibold">{geofence.name}</p>
                          <p className="text-gray-600">Raio: {geofence.radius || 500} m</p>
                          {geofence.address && (
                            <p className="text-gray-500 text-xs mt-1 truncate max-w-[200px]">
                              📍 {geofence.address}
                            </p>
                          )}
                        </div>
                      </Tooltip>
                    </Circle>
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
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Nome</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Tipo</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Raio</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Alertas</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Ações</th>
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
                        <p className="font-medium text-gray-900">{geofence.name}</p>
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                          ◯ Círculo
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-gray-600">{geofence.radius || 500} m</p>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
                          geofence.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          <span className={`w-2 h-2 rounded-full ${geofence.is_active ? 'bg-green-600' : 'bg-red-600'}`}></span>
                          {geofence.is_active ? 'Ativo' : 'Inativo'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex gap-2">
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                            geofence.alert_on_enter ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-600'
                          }`}>Entrada</span>
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                            geofence.alert_on_exit ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-600'
                          }`}>Saída</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <button onClick={(e) => { e.stopPropagation(); handleEdit(geofence) }} className="p-2 hover:bg-blue-50 text-blue-600 rounded-lg transition" title="Editar">
                            <Edit2 size={18} />
                          </button>
                          <button onClick={(e) => { e.stopPropagation(); handleDelete(geofence.id) }} className="p-2 hover:bg-red-50 text-red-600 rounded-lg transition" title="Deletar">
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

      {/* Modal de Criação/Edição */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-[9999]">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              {editingId ? 'Editar Geofence' : 'Novo Geofence'}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
                <input type="text" name="name" value={formData.name} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
                <textarea name="description" value={formData.description} onChange={handleChange} rows={2} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Raio (metros)</label>
                <input type="number" name="radius" value={formData.radius} onChange={handleChange} min="10" max="10000" required className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Localização (centro)</label>
                <button
                  type="button"
                  onClick={() => setShowLocationModal(true)}
                  className="w-full flex items-center justify-center gap-2 bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-4 rounded-lg transition"
                >
                  <Target size={16} />
                  {selectedPosition 
                    ? `Lat: ${selectedPosition[0].toFixed(4)}, Lng: ${selectedPosition[1].toFixed(4)}`
                    : 'Clique para selecionar a localização'}
                </button>
                {selectedPosition && (
                  <p className="text-green-600 text-xs mt-1">✓ Localização selecionada</p>
                )}
              </div>

              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-700">Alertas</p>
                <div className="flex items-center gap-2">
                  <input type="checkbox" id="alert_enter" name="alert_on_enter" checked={formData.alert_on_enter} onChange={handleChange} className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500" />
                  <label htmlFor="alert_enter" className="text-sm text-gray-700">Alerta ao entrar</label>
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" id="alert_exit" name="alert_on_exit" checked={formData.alert_on_exit} onChange={handleChange} className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500" />
                  <label htmlFor="alert_exit" className="text-sm text-gray-700">Alerta ao sair</label>
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button type="submit" className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition">
                  {editingId ? 'Atualizar' : 'Criar'}
                </button>
                <button type="button" onClick={handleCloseModal} className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-900 font-semibold py-2 px-4 rounded-lg transition">
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de Seleção de Localização */}
      <LocationSelectorModal
        isOpen={showLocationModal}
        onClose={() => setShowLocationModal(false)}
        onConfirm={handleConfirmLocation}
        initialLocation={selectedPosition || undefined}
      />
    </Layout>
  )
}