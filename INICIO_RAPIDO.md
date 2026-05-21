# 🚀 ISP Tracker Platform - Guia de Início Rápido

## ⚡ Requisitos (O que você precisa ter)

- [ ] **Git** - [Baixar](https://git-scm.com/)
- [ ] **Node.js 18+** - [Baixar](https://nodejs.org/)
- [ ] **Python 3.11+** - [Baixar](https://www.python.org/) ⚠️ **Marque "Add Python to PATH"**
- [ ] **WSL2** (opcional, para Linux no Windows) - [Guia](https://learn.microsoft.com/pt-br/windows/wsl/install)

---

## 📥 Passo 1: Clonar/Baixar o Projeto

### Se tiver Git:
```bash
git clone <seu-repositorio>
cd isp-tracker-platform
```

### Se não tiver Git:
1. Baixe o arquivo ZIP do projeto
2. Descompacte em uma pasta
3. Abra terminal nessa pasta

---

## 🔧 Passo 2: Instalar Dependências do Frontend

### No PowerShell (Windows) ou Terminal (Mac/Linux):

```bash
cd frontend

npm install
```

⏳ **Aguarde 2-3 minutos** enquanto instala os pacotes...

---

## 🐍 Passo 3: Instalar Dependências do Backend

### No PowerShell (Windows):

```bash
cd ../backend

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

### No Terminal (Mac/Linux ou WSL2):

```bash
cd ../backend

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

⏳ **Aguarde 2-3 minutos** enquanto instala os pacotes...

---

## ▶️ Passo 4: Rodar o Backend

### PowerShell (Windows):

```bash
# Dentro da pasta backend, com venv ativado
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Terminal (Mac/Linux/WSL2):

```bash
# Dentro da pasta backend, com venv ativado
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Deve aparecer:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

✅ **Backend rodando!**

---

## ▶️ Passo 5: Rodar o Frontend

### Abra UM NOVO terminal (não feche o do backend!)

```bash
cd frontend

npm run dev
```

**Deve aparecer:**
```
Local:   http://localhost:5173/
```

✅ **Frontend rodando!**

---

## 🌐 Passo 6: Acessar no Navegador

### Abra seu navegador (Chrome, Firefox, Edge, etc):

**Dashboard:** http://localhost:5173

**API Docs:** http://localhost:8000/docs

**Swagger:** http://localhost:8000/redoc

---

## 🔐 Passo 7: Fazer Login

### Credenciais padrão:

```
Email: admin@example.com
Senha: password123
```

### Se essas credenciais não funcionarem, crie uma nova conta:

1. Clique em "Registrar" na página de login
2. Preencha com seus dados
3. Clique em criar conta
4. Faça login com as novas credenciais

---

## 📊 Acessos Rápidos

| O quê | Link | Porta |
|-------|------|-------|
| **Dashboard (Interface)** | http://localhost:5173 | 5173 |
| **API Documentation** | http://localhost:8000/docs | 8000 |
| **Swagger UI** | http://localhost:8000/redoc | 8000 |
| **Health Check** | http://localhost:8000/health | 8000 |

---

## 🎯 O que você pode fazer agora

✅ Visualizar o Dashboard  
✅ Criar técnicos  
✅ Ver alertas  
✅ Criar geofences  
✅ Testar a API pelo Swagger  

---

## ❌ Problemas Comuns

### "python não é reconhecido"

**Solução:** Reinstale Python e **MARQUE "Add Python to PATH"**

Ou use `python3` em vez de `python`

### "npm não é reconhecido"

**Solução:** Reinstale Node.js

Depois feche e reabra o PowerShell

### "Porta 5173/8000 já está em uso"

**Solução:**

PowerShell:
```powershell
# Encontrar processo
netstat -ano | findstr :5173

# Matar processo (substitua PID)
taskkill /PID <PID> /F
```

Terminal Linux/Mac:
```bash
# Matar processo na porta
lsof -ti :5173 | xargs kill -9
```

### "Database connection error"

Isso é normal se não tiver PostgreSQL rodando. Os dados serão salvos em memória.

### Frontend branco/em branco

```bash
# Limpar cache
cd frontend
rm -rf node_modules
npm install
npm run dev
```

---

## 📝 Estrutura de Pastas

```
isp-tracker-platform/
├── frontend/          # React (Interface)
│   └── src/
├── backend/           # FastAPI (API)
│   └── app/
├── docs/              # Documentação
└── README.md
```

---

## 🔗 Próximas Features para Testar

- [ ] Criar um técnico novo
- [ ] Visualizar no mapa
- [ ] Criar geofence
- [ ] Ver alertas
- [ ] Testar API pelo Swagger

---

## 💡 Dicas Úteis

### Ver logs do backend:
```bash
# No terminal do backend, aparece em tempo real
```

### Resetar dados:
```bash
# Não temos banco real, então basta reiniciar o backend
# Dados em memória são perdidos
```

### Editar código e ver mudanças:
```bash
# Frontend: Salve o arquivo, atualiza automático no navegador
# Backend: Salve o arquivo, reinicia automático
```

---

## 🚀 Pronto para começar?

1. ✅ Instale os requisitos
2. ✅ Siga os passos 1-7
3. ✅ Acesse http://localhost:5173
4. ✅ Faça login
5. ✅ Explore!

---

## 📞 Dúvidas?

Consulte:
- `docs/API.md` - Referência completa da API
- `docs/ARCHITECTURE.md` - Arquitetura do projeto
- `docs/SETUP.md` - Guia avançado
- `QUICK_START.md` - Instruções rápidas

---

**Versão:** 1.0.0  
**Data:** 2026-05-19  
**Status:** ✅ Funcionando
