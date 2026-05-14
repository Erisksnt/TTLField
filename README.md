# ISP Tracker Platform 🚀

Plataforma corporativa de rastreamento e inteligência operacional para equipes técnicas externas de provedores de internet.

## 📋 Visão Geral

Sistema completo de:
- ✅ Rastreamento inteligente de técnicos via smartphone corporativo
- ✅ Dashboard administrativo web em tempo real
- ✅ Análise de rotas e telemetria operacional
- ✅ Geofencing e alertas automáticos
- ✅ Integração com ERP Auvo (preparado para futuro)

## 🏗️ Arquitetura

```
┌─────────────────────┐
│   App Mobile Tech   │ (Flutter)
│   - Rastreamento    │
│   - Silencioso      │
│   - Offline-first   │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  FastAPI Backend    │ (Python)
│  - API REST         │
│  - WebSocket RT     │
│  - Autenticação JWT │
└──────────┬──────────┘
           │
┌──────────▼──────────┐         ┌──────────────┐
│   PostgreSQL DB     │◄────────┤ Traccar GPS  │
│   - Posições        │         │ - Engine     │
│   - Técnicos        │         └──────────────┘
│   - Alertas         │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  React Dashboard    │ (TypeScript)
│  - Mapa RT          │
│  - Analytics        │
│  - Playback         │
└─────────────────────┘
```

## 📦 Stack Tecnológico

### Backend
- **Python 3.11** com FastAPI
- **PostgreSQL** para persistência
- **SQLAlchemy** ORM com async
- **JWT** para autenticação
- **WebSocket** para tempo real

### Frontend
- **React 18** com TypeScript
- **TailwindCSS** para styling
- **Vite** para build
- **Leaflet** para mapas
- **OpenStreetMap** para base de mapas

### Mobile
- **Flutter** para iOS/Android
- **Provider** para state management
- **Geolocator** para GPS
- **Background execution** para tracking silencioso

### Infraestrutura
- **Docker** & **Docker Compose** para orquestração
- **Traccar** como engine GPS
- Pronto para cloud (AWS, Azure, GCP)

## 🚀 Quick Start

### 1. Clonar e Configurar

```bash
git clone <repo>
cd isp-tracker-platform
cp .env.example .env
```

### 2. Iniciar com Docker Compose

```bash
docker-compose up -d
```

Isso inicia:
- PostgreSQL (porta 5432)
- FastAPI Backend (porta 8000)
- React Frontend (porta 5173)
- Traccar (porta 8082)

### 3. Acessar

- 📊 Dashboard: http://localhost:5173
- 🔌 API Docs: http://localhost:8000/docs
- 🗺️ Traccar: http://localhost:8082

## 📚 Documentação

- [Arquitetura](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Setup Detalhado](docs/SETUP.md)

## 🔐 Segurança

- ✅ JWT Authentication
- ✅ RBAC (Role-Based Access Control)
- ✅ HTTPS Ready
- ✅ LGPD Compliance
- ✅ Auditoria completa
- ✅ Retenção de dados configurável

## 🎯 Funcionalidades Principais

### Para Técnicos
- App mobile silencioso com rastreamento automático
- Login seguro com JWT
- Rastreamento adaptativo (bateria vs precisão)
- Sincronização offline-first

### Para Administrativos
- Dashboard em tempo real com mapa live
- Histórico de posições com playback
- Criação de geofences (círculos, polígonos)
- Alertas operacionais (velocidade, offline, bateria baixa)
- Relatórios e analytics
- Gerenciamento de técnicos e dispositivos

## 📊 Dados & Análise

- Distância percorrida
- Tempo parado vs movimentação
- SLA e produtividade
- Heatmaps de deslocamento
- Eventos operacionais
- Integração com Auvo (preparada)

## 🔄 Integração Futura

- API do Auvo para sync de OS
- Webhooks para eventos
- Sincronização de status operacional
- Relacionamento automático: técnico + localização + OS

## 📱 Multiplataforma

- ✅ Android (app mobile)
- ✅ iOS (app mobile)
- ✅ Desktop (navegador)
- ✅ Mobile web (navegador)
- ✅ Tablets

## 🛠️ Requisitos Mínimos

- Docker & Docker Compose
- 2GB RAM mínimo
- PostgreSQL 12+ (incluído no Docker)
- Navegador moderno (Chrome, Firefox, Safari, Edge)

## 📝 Licença

Proprietário - Todos os direitos reservados

## 👥 Suporte

- Issues: GitHub
- Email: suporte@isp-tracker.local

---

**Versão:** 1.0.0  
**Status:** Em desenvolvimento  
**Última atualização:** May 2026