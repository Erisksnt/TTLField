// frontend/src/components/Layout.tsx (versão com logo)
import { ReactNode, useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import {
  Menu,
  X,
  Home,
  Users,
  AlertCircle,
  MapPin,
  LogOut,
} from 'lucide-react'
import logoMenu from '@/assets/img/logo-menu.png'
import logoFooter from '@/assets/img/logo-footer.png'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const logout = useAuthStore((state) => state.logout)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  // Detectar mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
      if (window.innerWidth >= 768) {
        setSidebarOpen(true)
      } else {
        setSidebarOpen(false)
      }
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const navigationItems = [
    { path: '/', label: 'Dashboard', icon: Home },
    { path: '/technicians', label: 'Técnicos', icon: Users },
    { path: '/alerts', label: 'Alertas', icon: AlertCircle },
    { path: '/geofences', label: 'Geofences', icon: MapPin },
  ]

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Overlay para mobile quando sidebar está aberta */}
      {sidebarOpen && isMobile && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-20"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:relative z-30 bg-gray-900 text-white transition-all duration-300 h-full ${
          sidebarOpen ? 'w-64' : 'w-0 md:w-20 overflow-hidden'
        }`}
      >
        <div className="p-4 flex items-center justify-between">
          {sidebarOpen && (
            <img 
              src={logoFooter} 
              alt="Total Links Tracker" 
              className="h-14 w-auto"
            />
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1 hover:bg-gray-800 rounded ml-auto"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        <nav className="mt-8 space-y-2 px-4">
          {navigationItems.map((item) => {
            const Icon = item.icon
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => isMobile && setSidebarOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                  isActive(item.path)
                    ? 'bg-blue-600'
                    : 'hover:bg-gray-800'
                } ${!sidebarOpen && 'justify-center px-2'}`}
              >
                <Icon size={20} />
                {sidebarOpen && <span>{item.label}</span>}
              </Link>
            )
          })}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-800">
          <button
            onClick={handleLogout}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-gray-800 transition ${
              !sidebarOpen && 'justify-center'
            }`}
          >
            <LogOut size={20} />
            {sidebarOpen && <span>Sair</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar - Responsivo */}
        <header className="bg-white border-b border-gray-200 shadow-sm px-4 md:px-8 py-3 md:py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Botão menu mobile */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="md:hidden p-2 hover:bg-gray-100 rounded-lg"
            >
              <Menu size={20} />
            </button>
            <div className="text-gray-700">
              <img 
                src={logoMenu} 
                alt="Total Links Tracker" 
                className="h-8 md:h-14 w-auto"
              />
            </div>
          </div>
          <div className="flex items-center gap-2 md:gap-4">
            <span className="text-xs md:text-sm text-gray-600 hidden sm:inline">Administrator</span>
            <div className="w-8 h-8 md:w-10 md:h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold text-sm md:text-base">
              A
            </div>
          </div>
        </header>

        {/* Page Content - Responsivo */}
        <main className="flex-1 overflow-auto p-3 md:p-8">
          {children}
        </main>
      </div>
    </div>
  )
}