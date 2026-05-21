# Setup Detalhado - ISP Tracker Platform

## Pré-requisitos

### Sistema
- Linux/Mac/Windows com WSL
- Git
- Docker & Docker Compose

### Versões
- Docker: 20.10+
- Docker Compose: 2.0+
- Node.js: 18+
- Python: 3.11+

## Instalação Local (Development)

### 1. Clonar Repositório

```bash
git clone <repo-url> isp-tracker-platform
cd isp-tracker-platform
```

### 2. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar com valores da sua infraestrutura
# Valores padrão já estão bons para desenvolvimento
```

### 3. Iniciar com Docker Compose

```bash
# Build e iniciar todos os serviços
docker-compose up -d

# Verificar se todos estão rodando
docker-compose ps

# Ver logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 4. Aguardar Inicialização

```bash
# Esperar ~30s para o banco de dados estar pronto
# Backend iniciará automaticamente

# Verificar saúde do backend
curl http://localhost:8000/health
```

### 5. Acessar Aplicação

- **Dashboard**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **Traccar**: http://localhost:8082
- **PostgreSQL**: localhost:5432 (database client necessário)

### 6. Fazer Login

**Credenciais Demo:**
```
Email: admin@example.com
Senha: password123
```

Para criar novo usuário, acessar:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "seu@email.com",
    "username": "seu_usuario",
    "password": "senha_segura_123",
    "full_name": "Seu Nome"
  }'
```

## Desenvolvimento

### Backend

#### Setup Inicial

```bash
cd backend

# Criar virtual environment
python -m venv venv

# Ativar (Linux/Mac)
source venv/bin/activate

# Ativar (Windows)
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

#### Executar em Development

```bash
# Com auto-reload
uvicorn app.main:app --reload --port 8000

# Acessar swagger docs
open http://localhost:8000/docs
```

#### Criar Migrations (Alembic)

```bash
# Gerar migration automática
alembic revision --autogenerate -m "Descrição da mudança"

# Aplicar migrations
alembic upgrade head

# Reverter
alembic downgrade -1
```

#### Testes

```bash
# Executar testes
pytest

# Com cobertura
pytest --cov=app --cov-report=html

# Específico
pytest tests/test_auth.py -v
```

### Frontend

#### Setup Inicial

```bash
cd frontend

# Instalar dependências
npm install

# ou com yarn
yarn install
```

#### Executar em Development

```bash
# Dev server com hot reload
npm run dev

# Acessar
open http://localhost:5173
```

#### Build para Produção

```bash
npm run build

# Preview do build
npm run preview
```

#### Linting e Formatting

```bash
# Lint
npm run lint

# Format (com Prettier - adicionar se necessário)
npx prettier --write "src/**/*.{ts,tsx}"
```

## Troubleshooting

### Problema: Porta já em uso

```bash
# Encontrar processo usando a porta
lsof -i :8000
lsof -i :5173

# Matar processo
kill -9 <PID>
```

### Problema: Banco de dados não conecta

```bash
# Verificar se postgres está rodando
docker-compose logs postgres

# Reiniciar
docker-compose restart postgres

# Limpar volumes (⚠️ apaga dados)
docker-compose down -v
docker-compose up -d
```

### Problema: Frontend não consegue conectar à API

```bash
# Verificar se backend está rodando
curl http://localhost:8000/health

# Verificar CORS settings em app/config.py
# Adicionar frontend URL se necessário
```

### Problema: Dependências com problema

```bash
# Limpar cache npm
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# Ou Python
pip cache purge
pip install -r requirements.txt --force-reinstall
```

## Estrutura de Branches

```
main                    # Produção (stable)
  ├── develop          # Desenvolvimento (staging)
  │   ├── feature/...  # Novas features
  │   ├── fix/...      # Correções
  │   └── chore/...    # Manutenção
```

## Commits Convencionais

```
feat: nova feature
fix: correção de bug
docs: atualização de documentação
style: formatação de código
refactor: refatoração de código
perf: melhoria de performance
test: adição de testes
chore: tarefas de manutenção
```

## CI/CD Setup

### GitHub Actions

Criar arquivo `.github/workflows/main.yml`:

```yaml
name: CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ develop ]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm install
      - run: npm run lint
      - run: npm run build

  deploy:
    if: github.ref == 'refs/heads/main'
    needs: [test-backend, test-frontend]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          # Seu script de deploy
          echo "Deploying to production..."
```

## Ambiente de Staging

```bash
# Criar arquivo docker-compose.staging.yml
# com configurações para staging
docker-compose -f docker-compose.staging.yml up -d
```

## Monitoramento

### Logs em Produção

```bash
# Ver logs de todos os serviços
docker-compose logs -f

# Apenas backend
docker-compose logs -f backend

# Com timestamps
docker-compose logs --timestamps -f
```

### Health Checks

```bash
# Backend
curl -X GET http://localhost:8000/health

# Frontend
curl -I http://localhost:5173

# Database
docker-compose exec postgres pg_isready -U tracker_user
```

## Backup & Restore

### Backup do Banco de Dados

```bash
# Fazer dump
docker-compose exec postgres pg_dump -U tracker_user isp_tracker > backup.sql

# Comprimir
gzip backup.sql
```

### Restore do Banco de Dados

```bash
# Descomprimir
gunzip backup.sql.gz

# Restaurar
docker-compose exec -T postgres psql -U tracker_user isp_tracker < backup.sql
```

## Performance Tuning

### Backend
```python
# Em app/config.py
DATABASE_POOL_SIZE=20  # Aumentar para mais conexões
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_RECYCLE=3600
```

### Frontend
```javascript
// Vite config
build: {
  minify: 'terser',
  terserOptions: {
    compress: {
      drop_console: true
    }
  }
}
```

### Database
```sql
-- Criar índices adicionais conforme necessário
CREATE INDEX idx_positions_technician_desc ON positions(technician_id, timestamp DESC);
CREATE INDEX idx_alerts_technician_active ON alerts(technician_id) WHERE is_active = true;
```

## Upgrade de Versões

### Python Packages

```bash
# Verificar atualizações
pip list --outdated

# Atualizar específico
pip install --upgrade fastapi

# Atualizar requirements.txt
pip freeze > backend/requirements.txt
```

### Node Packages

```bash
# Verificar atualizações
npm outdated

# Atualizar específico
npm install react@latest

# Atualizar tudo
npm update
```

## Dúvidas Frequentes

### P: Como resetar o banco de dados?
R: `docker-compose down -v && docker-compose up -d`

### P: Como acessar o terminal do container?
R: `docker-compose exec backend bash`

### P: Como mudar a porta?
R: Editar `.env` ou `docker-compose.yml`

### P: Posso usar em produção assim?
R: Não. Ver seção de Deployment e segurança.

## Próximos Passos

1. ✅ Setup local concluído
2. ☐ Explorar API em http://localhost:8000/docs
3. ☐ Criar técnicos de teste
4. ☐ Simular rastreamento mobile
5. ☐ Configurar alertas
6. ☐ Criar geofences

## Suporte

- 📧 Email: suporte@isp-tracker.local
- 💬 Issues: GitHub
- 📚 Docs: `/docs`
