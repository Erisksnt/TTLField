# API Reference - ISP Tracker Platform

## Base URL

```
Development: http://localhost:8000
Production: https://api.isp-tracker.com
```

## Authentication

Todos os endpoints (exceto `/auth/*` e `/health`) requerem autenticação via JWT.

### Header Required

```
Authorization: Bearer <access_token>
```

## Endpoints

### 1. Authentication

#### Register User
```
POST /auth/register
Content-Type: application/json

{
  "email": "usuario@example.com",
  "username": "usuario123",
  "password": "senha_segura_123",
  "full_name": "Nome do Usuário",
  "role": "admin"
}

Response 201:
{
  "message": "Usuário registrado com sucesso",
  "user_id": "uuid-aqui"
}
```

#### Login
```
POST /auth/login
Content-Type: application/json

{
  "email": "usuario@example.com",
  "password": "senha_segura_123"
}

Response 200:
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Refresh Token
```
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGc..."
}

Response 200:
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Get Current User
```
GET /auth/me
Authorization: Bearer <token>

Response 200:
{
  "id": "uuid-here",
  "email": "usuario@example.com"
}
```

### 2. Technicians

#### List Technicians
```
GET /technicians?is_online=true&skip=0&limit=100
Authorization: Bearer <token>

Query Parameters:
- is_online: boolean (optional) - Filtrar por status online
- skip: integer - Paginação offset
- limit: integer - Itens por página

Response 200: [ Technician[] ]
```

#### Create Technician
```
POST /technicians
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "João Silva",
  "employee_id": "EMP-12345",
  "email": "joao@company.com",
  "phone": "11999999999",
  "cpf": "12345678900",
  "notes": "Técnico de field service"
}

Response 201: Technician
```

#### Get Technician Details
```
GET /technicians/{technician_id}
Authorization: Bearer <token>

Response 200: Technician
```

#### Update Technician
```
PATCH /technicians/{technician_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "João Silva Updated",
  "phone": "11988888888",
  "is_active": true
}

Response 200: Technician
```

#### Delete Technician
```
DELETE /technicians/{technician_id}
Authorization: Bearer <token>

Response 204: (No Content)
```

### 3. Positions (GPS Tracking)

#### Create Position
```
POST /positions?technician_id=uuid&device_id=uuid
Authorization: Bearer <token>
Content-Type: application/json

{
  "latitude": -23.5505,
  "longitude": -46.6333,
  "accuracy": 5.2,
  "altitude": 750.5,
  "speed": 45.3,
  "heading": 180.0,
  "battery_level": 85,
  "battery_status": "charging",
  "provider": "gps"
}

Response 201: Position
```

#### Bulk Create Positions
```
POST /positions/bulk?technician_id=uuid&device_id=uuid
Authorization: Bearer <token>
Content-Type: application/json

{
  "positions": [
    {
      "latitude": -23.5505,
      "longitude": -46.6333,
      "accuracy": 5.2,
      ...
    },
    ...
  ]
}

Response 201:
{
  "message": "5 posições salvas",
  "count": 5,
  "positions": [Position[]]
}
```

#### Get Technician Position History
```
GET /positions/{technician_id}?hours=24&limit=1000
Authorization: Bearer <token>

Query Parameters:
- hours: integer - Últimas N horas (1-730)
- limit: integer - Limite de registros

Response 200: [Position]
```

#### Get All Current Positions
```
GET /positions/current/all
Authorization: Bearer <token>

Response 200: 
[
  {
    "id": "uuid",
    "name": "João Silva",
    "latitude": -23.5505,
    "longitude": -46.6333,
    "is_online": true,
    "battery_level": 85,
    "last_seen": "2024-01-15T10:30:00Z"
  }
]
```

#### Calculate Distance Traveled
```
GET /positions/{technician_id}/distance?start_datetime=2024-01-15T08:00:00Z&end_datetime=2024-01-15T17:00:00Z
Authorization: Bearer <token>

Response 200:
{
  "technician_id": "uuid",
  "start_datetime": "2024-01-15T08:00:00Z",
  "end_datetime": "2024-01-15T17:00:00Z",
  "distance_km": 45.32
}
```

### 4. Geofences

#### List Geofences
```
GET /geofences
Authorization: Bearer <token>

Response 200: [Geofence[]]
```

#### Create Geofence
```
POST /geofences
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Escritório Principal",
  "description": "Localização principal da empresa",
  "geofence_type": "circle",
  "geometry": {
    "type": "Point",
    "coordinates": [-46.6333, -23.5505]
  },
  "radius": 500,
  "alert_on_enter": true,
  "alert_on_exit": true
}

Response 201: Geofence
```

#### Update Geofence
```
PATCH /geofences/{geofence_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Escritório Principal Updated",
  "alert_on_enter": false
}

Response 200: Geofence
```

#### Delete Geofence
```
DELETE /geofences/{geofence_id}
Authorization: Bearer <token>

Response 204: (No Content)
```

### 5. Alerts

#### List Alerts
```
GET /alerts?technician_id=uuid&alert_type=speeding&severity=high&is_active=true&limit=100&offset=0
Authorization: Bearer <token>

Query Parameters:
- technician_id: string (optional)
- alert_type: string (optional)
- severity: string (optional) - low, medium, high, critical
- is_active: boolean (optional)
- is_acknowledged: boolean (optional)
- limit: integer
- offset: integer

Response 200: [Alert[]]
```

#### Acknowledge Alert
```
POST /alerts/{alert_id}/acknowledge
Authorization: Bearer <token>
Content-Type: application/json

{
  "acknowledged_by": "admin-uuid"
}

Response 200: Alert (com is_acknowledged = true)
```

### 6. Health & Misc

#### Health Check
```
GET /health

Response 200:
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

#### API Root
```
GET /

Response 200:
{
  "message": "Bem-vindo ao ISP Tracker Platform",
  "version": "1.0.0",
  "docs": "/docs"
}
```

## Data Types

### Technician
```typescript
{
  id: string
  name: string
  employee_id: string
  email?: string
  phone?: string
  cpf?: string
  is_active: boolean
  is_online: boolean
  latitude?: number
  longitude?: number
  accuracy?: number
  battery_level?: number
  device_id?: string
  created_at: string (ISO 8601)
  updated_at: string (ISO 8601)
  last_seen?: string (ISO 8601)
}
```

### Position
```typescript
{
  id: string
  technician_id: string
  device_id: string
  latitude: number (-90 to 90)
  longitude: number (-180 to 180)
  accuracy?: number (meters)
  altitude?: number (meters)
  speed?: number (km/h)
  heading?: number (degrees)
  battery_level?: number (0-100)
  battery_status?: string
  provider: string (gps|network|fused)
  is_valid: boolean
  timestamp: string (ISO 8601)
  received_at: string (ISO 8601)
}
```

### Alert
```typescript
{
  id: string
  technician_id: string
  device_id: string
  geofence_id?: string
  alert_type: string
  title: string
  description?: string
  severity: "low" | "medium" | "high" | "critical"
  is_active: boolean
  is_acknowledged: boolean
  acknowledged_at?: string (ISO 8601)
  acknowledged_by?: string
  metadata?: Record<string, any>
  triggered_at: string (ISO 8601)
  resolved_at?: string (ISO 8601)
  created_at: string (ISO 8601)
}
```

### Geofence
```typescript
{
  id: string
  name: string
  description?: string
  geofence_type: "circle" | "polygon" | "rectangle"
  geometry: Record<string, any> (GeoJSON)
  is_active: boolean
  alert_on_enter: boolean
  alert_on_exit: boolean
  created_at: string (ISO 8601)
  updated_at: string (ISO 8601)
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Descrição do erro de validação"
}
```

### 401 Unauthorized
```json
{
  "detail": "Token inválido ou expirado"
}
```

### 403 Forbidden
```json
{
  "detail": "Permissão negada"
}
```

### 404 Not Found
```json
{
  "detail": "Recurso não encontrado"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Erro interno do servidor"
}
```

## Rate Limiting

Não implementado por padrão, mas pode ser adicionado com middleware.

## WebSocket

```javascript
// Conectar
const ws = new WebSocket('ws://localhost:8000/ws/{technician_id}');

// Escutar mensagens
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.event);
};

// Eventos possíveis
{
  "event": "position_update",
  "technician_id": "uuid",
  "latitude": -23.5505,
  "longitude": -46.6333,
  "timestamp": "2024-01-15T10:30:00Z"
}

{
  "event": "alert_triggered",
  "alert_id": "uuid",
  "alert_type": "speeding",
  "severity": "high"
}

{
  "event": "geofence_event",
  "geofence_id": "uuid",
  "event_type": "enter",
  "technician_id": "uuid"
}
```

## Exemplos de Integração

### cURL

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "password123"
  }'

# Listar técnicos
curl -X GET http://localhost:8000/technicians \
  -H "Authorization: Bearer eyJhbGc..."

# Criar posição
curl -X POST "http://localhost:8000/positions?technician_id=uuid&device_id=uuid" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": -23.5505,
    "longitude": -46.6333,
    "accuracy": 5.2,
    "battery_level": 85
  }'
```

### Python Requests

```python
import requests

BASE_URL = "http://localhost:8000"
headers = {"Authorization": f"Bearer {token}"}

# Listar técnicos
response = requests.get(f"{BASE_URL}/technicians", headers=headers)
technicians = response.json()

# Criar posição
data = {
    "latitude": -23.5505,
    "longitude": -46.6333,
    "accuracy": 5.2,
    "battery_level": 85
}
response = requests.post(
    f"{BASE_URL}/positions?technician_id=uuid&device_id=uuid",
    json=data,
    headers=headers
)
```

### JavaScript Fetch

```javascript
const API_URL = 'http://localhost:8000';
const token = localStorage.getItem('access_token');

// Listar técnicos
fetch(`${API_URL}/technicians`, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(res => res.json())
.then(data => console.log(data));

// Criar posição
fetch(`${API_URL}/positions?technician_id=uuid&device_id=uuid`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    latitude: -23.5505,
    longitude: -46.6333,
    accuracy: 5.2,
    battery_level: 85
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

## Status Codes

| Código | Significado |
|--------|-------------|
| 200    | OK - Requisição bem-sucedida |
| 201    | Created - Recurso criado |
| 204    | No Content - Recurso deletado |
| 400    | Bad Request - Dados inválidos |
| 401    | Unauthorized - Token inválido |
| 403    | Forbidden - Sem permissão |
| 404    | Not Found - Recurso não encontrado |
| 500    | Server Error - Erro no servidor |

## Testes da API

### Swagger UI
Abra http://localhost:8000/docs para testar todos os endpoints interativamente.

### Postman
Importar a coleção de endpoints do Swagger: http://localhost:8000/openapi.json

## Versionamento

A API está na **v1**. Mudanças breaking virão em v2+ com deprecation notices antecipados.
