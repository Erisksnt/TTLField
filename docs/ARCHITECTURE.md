# Arquitetura - ISP Tracker Platform

## Visão Geral

A ISP Tracker Platform é uma solução modular e escalável para rastreamento operacional de técnicos externos em tempo real.

## Componentes Principais

```
┌─────────────────────────────────────────────────────────────┐
│                    ISP Tracker Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Mobile App   │  │  Dashboard   │  │ Admin Panel  │       │
│  │  (Flutter)   │  │   (React)    │  │  (React)     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│         ┌──────────────────▼──────────────────┐              │
│         │    API Gateway / FastAPI Backend    │              │
│         │  - Authentication (JWT)             │              │
│         │  - WebSocket (Real-time)            │              │
│         │  - REST API                         │              │
│         └──────────────────┬──────────────────┘              │
│                            │                                 │
│         ┌──────────────────┴──────────────────┐              │
│         │                                     │              │
│    ┌────▼────┐  ┌─────────────┐  ┌──────────▼──┐            │
│    │PostgreSQL  │  │Traccar GPS │  │Redis Cache │            │
│    └────────┘  └─────────────┘  └────────────┘            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 1. Frontend (React + TypeScript)

### Estrutura de Pastas

```
frontend/src/
├── components/          # Componentes reutilizáveis
│   ├── Layout.tsx       # Layout principal
│   └── ProtectedRoute.tsx
├── pages/              # Páginas da aplicação
│   ├── LoginPage.tsx
│   ├── DashboardPage.tsx
│   ├── TechniciansPage.tsx
│   ├── AlertsPage.tsx
│   └── GeofencesPage.tsx
├── hooks/              # Hooks customizados
│   ├── useAuth.ts
│   └── useRequest.ts
├── services/           # Serviços de API
│   └── api.ts
├── store/              # State management (Zustand)
│   └── auth.ts
├── types/              # Tipos TypeScript
│   └── index.ts
└── utils/              # Utilitários
```

### Principais Tecnologias

- **React 18**: UI library
- **TypeScript**: Tipagem estática
- **Vite**: Build tool (dev server rápido)
- **TailwindCSS**: Styling
- **React Router**: Routing
- **Axios**: HTTP client
- **Zustand**: State management
- **Leaflet**: Mapas
- **Recharts**: Gráficos
- **React Hot Toast**: Notificações

### Padrões

- **Smart Components**: Páginas com lógica de dados
- **Dumb Components**: Componentes reutilizáveis puros
- **Hooks**: Lógica reutilizável
- **Context/Store**: Estado global

## 2. Backend (FastAPI + Python)

### Estrutura de Pastas

```
backend/app/
├── main.py             # Entrada da aplicação
├── config.py           # Configurações
├── database.py         # Setup do banco de dados
├── models/             # Models SQLAlchemy
│   ├── user.py
│   ├── technician.py
│   ├── device.py
│   ├── position.py
│   ├── geofence.py
│   ├── alert.py
│   └── event.py
├── schemas/            # Schemas Pydantic (validation/serialization)
│   ├── user.py
│   ├── technician.py
│   ├── position.py
│   ├── geofence.py
│   └── alert.py
├── routes/             # Rotas API
│   ├── auth.py
│   ├── technicians.py
│   ├── devices.py
│   ├── positions.py
│   ├── geofences.py
│   └── alerts.py
├── services/           # Lógica de negócio
│   ├── auth_service.py
│   ├── tracking_service.py
│   ├── geofence_service.py
│   └── alert_service.py
├── websocket/          # WebSocket handlers
│   ├── manager.py
│   └── handlers.py
└── utils/              # Utilitários
    ├── jwt.py
    └── security.py
```

### Principais Tecnologias

- **FastAPI**: Web framework (async)
- **SQLAlchemy**: ORM
- **Pydantic**: Data validation
- **PostgreSQL**: Database
- **asyncpg**: Async DB driver
- **python-jose**: JWT handling
- **Passlib**: Password hashing
- **WebSockets**: Real-time updates

### Padrões

- **MVC Pattern**: Models, Views (Routes), Controllers (Services)
- **Dependency Injection**: FastAPI Depends
- **Async/Await**: Operações assíncronas
- **Type Hints**: Tipagem completa em Python

## 3. Banco de Dados (PostgreSQL)

### Schema

#### Tabela: users
```sql
- id (UUID, PK)
- email (VARCHAR, UNIQUE)
- username (VARCHAR, UNIQUE)
- hashed_password (VARCHAR)
- full_name (VARCHAR)
- role (ENUM: user, manager, admin, supervisor)
- is_active (BOOLEAN)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- last_login (TIMESTAMP)
```

#### Tabela: technicians
```sql
- id (UUID, PK)
- employee_id (VARCHAR, UNIQUE)
- name (VARCHAR)
- email (VARCHAR)
- phone (VARCHAR)
- cpf (VARCHAR, UNIQUE)
- is_active (BOOLEAN)
- is_online (BOOLEAN)
- last_seen (TIMESTAMP)
- latitude (FLOAT)
- longitude (FLOAT)
- accuracy (FLOAT)
- battery_level (INTEGER)
- device_id (FK)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

#### Tabela: devices
```sql
- id (UUID, PK)
- device_id (VARCHAR, UNIQUE)
- imei (VARCHAR, UNIQUE)
- device_name (VARCHAR)
- device_model (VARCHAR)
- os_type (VARCHAR)
- os_version (VARCHAR)
- is_active (BOOLEAN)
- is_tracking (BOOLEAN)
- last_heartbeat (TIMESTAMP)
- tracking_interval (INTEGER)
- app_version (VARCHAR)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

#### Tabela: positions
```sql
- id (UUID, PK)
- technician_id (FK)
- device_id (FK)
- latitude (FLOAT)
- longitude (FLOAT)
- accuracy (FLOAT)
- altitude (FLOAT)
- speed (FLOAT)
- heading (FLOAT)
- battery_level (INTEGER)
- provider (VARCHAR)
- timestamp (TIMESTAMP, INDEXED)
- received_at (TIMESTAMP)
- is_valid (BOOLEAN)

INDEXES:
- idx_technician_timestamp (technician_id, timestamp)
- idx_device_timestamp (device_id, timestamp)
- idx_timestamp (timestamp)
```

#### Tabela: geofences
```sql
- id (UUID, PK)
- name (VARCHAR)
- description (TEXT)
- geofence_type (ENUM: circle, polygon, rectangle)
- geometry (JSON)
- center_latitude (FLOAT)
- center_longitude (FLOAT)
- radius (INTEGER)
- is_active (BOOLEAN)
- alert_on_enter (BOOLEAN)
- alert_on_exit (BOOLEAN)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

#### Tabela: alerts
```sql
- id (UUID, PK)
- technician_id (FK)
- device_id (FK)
- geofence_id (FK, NULLABLE)
- alert_type (VARCHAR)
- title (VARCHAR)
- description (TEXT)
- severity (ENUM: low, medium, high, critical)
- is_active (BOOLEAN)
- is_acknowledged (BOOLEAN)
- acknowledged_at (TIMESTAMP)
- acknowledged_by (VARCHAR)
- metadata (JSON)
- triggered_at (TIMESTAMP, INDEXED)
- resolved_at (TIMESTAMP)
- created_at (TIMESTAMP)
```

#### Tabela: events
```sql
- id (UUID, PK)
- technician_id (FK)
- device_id (FK)
- geofence_id (FK, NULLABLE)
- event_type (VARCHAR)
- title (VARCHAR)
- description (TEXT)
- metadata (JSON)
- event_timestamp (TIMESTAMP, INDEXED)
- created_at (TIMESTAMP)
```

## 4. Fluxo de Autenticação

```
┌─────────────┐
│  User       │
└──────┬──────┘
       │ POST /auth/login
       │ { email, password }
       ▼
┌─────────────────────────┐
│  Backend: login()       │
│  - Validate password    │
│  - Generate tokens      │
└──────┬──────────────────┘
       │
       │ Response:
       │ - access_token (30 min)
       │ - refresh_token (7 days)
       │
       ▼
┌─────────────┐
│  Client     │
│  - Store tokens in localStorage
│  - Add to every request header
└─────────────┘
```

## 5. Fluxo de Rastreamento

```
┌──────────────────┐
│  Mobile App      │ (5-30s interval)
│  - Coleta GPS    │
│  - Bateria       │
│  - Status        │
└────────┬─────────┘
         │ POST /positions
         │
         ▼
┌──────────────────┐
│  Backend         │
│  - Valida dados  │
│  - Persiste DB   │
│  - Atualiza Auvo │
│  - Emite eventos │
└────────┬─────────┘
         │
    ┌────┴──────┬──────────┐
    │            │          │
    ▼            ▼          ▼
┌────────┐ ┌─────────┐ ┌──────────┐
│ Database│ │WebSocket│ │Alertas   │
│ Position│ │Real-time│ │(Triggers)│
└────────┘ └─────────┘ └──────────┘
```

## 6. API Endpoints

### Authentication
- `POST /auth/register` - Registrar usuário
- `POST /auth/login` - Fazer login
- `POST /auth/refresh` - Renovar token
- `GET /auth/me` - Dados do usuário atual

### Technicians
- `GET /technicians` - Listar técnicos
- `POST /technicians` - Criar técnico
- `GET /technicians/{id}` - Obter detalhes
- `PATCH /technicians/{id}` - Atualizar
- `DELETE /technicians/{id}` - Deletar

### Positions
- `POST /positions` - Criar posição
- `POST /positions/bulk` - Batch de posições
- `GET /positions/{technician_id}` - Histórico
- `GET /positions/current/all` - Posições atuais
- `GET /positions/{technician_id}/distance` - Distância percorrida

### Geofences
- `GET /geofences` - Listar geofences
- `POST /geofences` - Criar geofence
- `PATCH /geofences/{id}` - Atualizar
- `DELETE /geofences/{id}` - Deletar

### Alerts
- `GET /alerts` - Listar alertas
- `POST /alerts/{id}/acknowledge` - Reconhecer alerta

## 7. WebSocket Events

```javascript
// Cliente conecta
ws://backend:8000/ws/{technician_id}

// Eventos transmitidos
{
  "event": "position_update",
  "technician_id": "xxx",
  "latitude": -23.55,
  "longitude": -46.63,
  "timestamp": "2024-01-01T10:00:00Z"
}

{
  "event": "alert_triggered",
  "alert_type": "speeding",
  "severity": "high",
  "technician_id": "xxx"
}

{
  "event": "geofence_event",
  "geofence_id": "yyy",
  "event_type": "enter",
  "technician_id": "xxx"
}
```

## 8. Segurança

### JWT Tokens
- **Access Token**: 30 minutos de validade
- **Refresh Token**: 7 dias de validade
- **Algorithm**: HS256

### Password Hashing
- **Algorithm**: bcrypt
- **Rounds**: 12

### HTTPS
- Todas as requisições em produção devem usar HTTPS
- Certificados SSL/TLS obrigatórios

### CORS
- Configurável por ambiente
- Whitelist de domínios permitidos

## 9. Deployment

### Docker Compose (Development)
```bash
docker-compose up -d
```

### Prod (AWS/Azure/GCP)
- Backend: Container em Kubernetes ou ECS
- Database: Managed PostgreSQL (RDS, Cloud SQL, etc)
- Frontend: CDN (CloudFront, Azure CDN, Cloudflare)
- Storage: S3, Blob Storage, etc

## 10. Monitoramento e Logging

### Logs
- Estruturados em JSON
- Níveis: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Persistência: CloudWatch, ELK, etc

### Métricas
- Prometheus-ready
- Grafana para visualização
- Alertas baseados em thresholds

## 11. Escalabilidade

### Horizontally
- Backend: Múltiplas instâncias atrás de load balancer
- Database: Read replicas + sharding se necessário
- Cache: Redis para sessões e cache

### Vertically
- Database: Aumentar CPU/RAM
- Backend: Otimizações de código
- Frontend: CDN + compression

## Referências

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Pydantic Docs](https://docs.pydantic.dev/)
