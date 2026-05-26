// frontend/src/pages/RegisterPage.tsx
import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '@/services/api'
import toast from 'react-hot-toast'

export default function RegisterPage() {
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [errors, setErrors] = useState<{ [key: string]: string }>({})
  const navigate = useNavigate()

  const validateForm = () => {
    const newErrors: { [key: string]: string } = {}
    
    if (!fullName.trim()) {
      newErrors.fullName = 'Nome é obrigatório'
    } else if (fullName.trim().length < 3) {
      newErrors.fullName = 'Nome deve ter pelo menos 3 caracteres'
    }
    
    if (!username.trim()) {
      newErrors.username = 'Usuário é obrigatório'
    } else if (username.length < 3) {
      newErrors.username = 'Usuário deve ter pelo menos 3 caracteres'
    } else if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      newErrors.username = 'Use apenas letras, números e "underscore"'
    }
    
    if (!email.trim()) {
      newErrors.email = 'E-mail é obrigatório'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = 'E-mail inválido (ex: nome@empresa.com)'
    }
    
    if (!password) {
      newErrors.password = 'Senha é obrigatória'
    } else if (password.length < 8) {
      newErrors.password = 'Senha deve ter pelo menos 8 caracteres'
    } else if (!/[A-Z]/.test(password)) {
      newErrors.password = 'Senha deve ter pelo menos uma letra maiúscula'
    } else if (!/[a-z]/.test(password)) {
      newErrors.password = 'Senha deve ter pelo menos uma letra minúscula'
    } else if (!/[0-9]/.test(password)) {
      newErrors.password = 'Senha deve ter pelo menos um número'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }
    
    try {
      setIsLoading(true)
      
      const payload = {
        email: email.trim(),
        username: username.trim(),
        password: password,
        full_name: fullName.trim()
      }
      
      const response = await api.register(payload)
      
      toast.success('Conta criada com sucesso! Faça login.')
      navigate('/login')
    } catch (error: any) {
      console.error('Erro no registro:', error.response?.data)
      
      // Tratar erro do backend
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail
        
        if (Array.isArray(detail) && detail.length > 0) {
          const firstError = detail[0]
          const field = firstError.loc?.pop()
          let message = firstError.msg
          
          // Traduzir mensagens comuns
          if (message.includes('valid email')) {
            message = 'E-mail inválido'
          } else if (message.includes('longer than')) {
            message = 'Campo muito longo'
          } else if (message.includes('shorter than')) {
            message = 'Campo muito curto'
          }
          
          if (field && message) {
            setErrors({ [field]: message })
          } else {
            toast.error(message)
          }
        } else if (typeof detail === 'string' && detail.includes('já cadastrado')) {
          if (detail.includes('email')) {
            setErrors({ email: 'Este e-mail já está cadastrado' })
          } else if (detail.includes('username')) {
            setErrors({ username: 'Este usuário já existe' })
          } else {
            toast.error(detail)
          }
        } else {
          toast.error('Erro ao criar conta. Tente novamente.')
        }
      } else {
        toast.error('Erro ao criar conta. Tente novamente.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-md p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Criar Conta</h1>
        <p className="text-gray-600 mb-6">Registre-se na plataforma</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nome Completo
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => {
                setFullName(e.target.value)
                if (errors.fullName) setErrors({ ...errors, fullName: '' })
              }}
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none ${
                errors.fullName ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Seu nome"
            />
            {errors.fullName && (
              <p className="text-red-500 text-xs mt-1">{errors.fullName}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Usuário
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => {
                setUsername(e.target.value)
                if (errors.username) setErrors({ ...errors, username: '' })
              }}
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none ${
                errors.username ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="seu_usuario"
            />
            {errors.username ? (
              <p className="text-red-500 text-xs mt-1">{errors.username}</p>
            ) : (
              <p className="text-gray-500 text-xs mt-1">Apenas letras, números e _</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              E-mail
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value)
                if (errors.email) setErrors({ ...errors, email: '' })
              }}
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none ${
                errors.email ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="seu@email.com"
            />
            {errors.email && (
              <p className="text-red-500 text-xs mt-1">{errors.email}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Senha
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value)
                if (errors.password) setErrors({ ...errors, password: '' })
              }}
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none ${
                errors.password ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="••••••••"
            />
            {errors.password ? (
              <p className="text-red-500 text-xs mt-1">{errors.password}</p>
            ) : (
              <p className="text-gray-500 text-xs mt-1">Mínimo 8 caracteres, com letras maiúsculas, minúsculas e números</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition disabled:opacity-50"
          >
            {isLoading ? 'Criando conta...' : 'Criar Conta'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-600 text-sm">
            Já tem conta?{' '}
            <Link to="/login" className="text-blue-600 hover:text-blue-700 font-semibold">
              Fazer login
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}