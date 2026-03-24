# Agent Backend LangGraph

Backend padrão LangGraph para expor agentes com API REST completa e persistência PostgreSQL.

## Estrutura do Projeto

```
agent_backend_langgraph/
├── langgraph.json              # Configuração do servidor LangGraph
├── .env                       # Variáveis de ambiente
├── requirements.txt            # Dependências
├── README.md                   # Este arquivo
└── src/agent/
    ├── __init__.py
    ├── webapp.py              # Custom routes e middleware
    ├── planning_graph.py      # Graph do agente de planning
    ├── research_graph.py      # Graph do agente de research
    ├── planning_agent/        # Módulo do agente de planning
    │   ├── __init__.py
    │   ├── prompts.py
    │   └── tools.py
    ├── research_agent/        # Módulo do agente de research
    │   ├── __init__.py
    │   ├── prompts.py
    │   └── tools.py
    └── skills/               # Skills do agente de planning
        ├── fasapi-projects-lister/
        ├── fasapi-tasks-manager/
        ├── fasapi-documents-manager/
        ├── sprint-planner/
        └── ardic-gin-expert/
```

## Agentes Disponíveis

| ID | Nome | Descrição |
|----|------|-----------|
| `planning` | Planning Agent | Agente de planejamento estratégico com ferramentas para gerenciar projetos, tarefas e documentos na JP BDC API |
| `research` | Research Agent | Agente de pesquisa profunda com sub-agentes para delegation |

## Quick Start

### 1. Instalação de Dependências

```bash
# Certifique-se de que o ambiente virtual está ativo
source .venv/bin/activate
```

### 2. Configurar Variáveis de Ambiente

Edite o arquivo `.env`:

```bash
# Banco de dados PostgreSQL
DATABASE_URL=postgresql://agent_user:password123@localhost:5432/deepagents

# Persistência LangGraph via PostgreSQL
POSTGRES_URI=postgresql://agent_user:password123@localhost:5432/deepagents

# API Keys
OPENAI_API_KEY=sk-...
OPENAI_API_BASE=https://openrouter.ai/api/v1
TAVILY_API_KEY=...

# JP BDC API (para tools do Planning Agent)
BDC_BASE_URL=http://localhost:8100
BDC_PASSKEY=your_passkey_here
```

### 3. Iniciar o Servidor

```bash
# Desenvolvimento (use o script de inicialização)
cd agent_backend_langgraph
./run.sh

# Ou manualmente com PYTHONPATH:
PYTHONPATH="src:src/agent:$PYTHONPATH" langgraph dev --port 8101 --no-browser
```

O servidor estará disponível em:
- **API**: http://localhost:8101
- **Docs**: http://localhost:8101/docs

### 4. Conectar o Frontend deep-agents-ui

No diálogo de configuração do frontend:

- **Deployment URL**: `http://localhost:8101`
- **Assistant ID**: `planning` ou `research`

## Produção

### Docker

```bash
# Build da imagem
langgraph build -t my-agent

# Run
docker run --env-file .env -p 8101:8000 my-agent
```

### Docker Compose

```yaml
# docker-compose.yml
services:
  agent:
    build: .
    ports:
      - "8101:8000"
    env_file: .env
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/deepagents
      - POSTGRES_URI=postgresql://user:pass@postgres:5432/deepagents
```

### Kubernetes

Consulte a [documentação oficial LangGraph](https://docs.langchain.com/langgraph-platform/deploy-standalone-server) para deployment com Helm.

## Adicionar Novo Agente

### Passo 1: Criar o diretório do agente

Crie um novo diretório em `src/agent/<nome>_agent/`:

```
src/agent/novo_agent/
├── __init__.py
├── prompts.py
└── tools.py
```

### Passo 2: Criar o arquivo do graph

Crie um novo arquivo em `src/agent/<nome>_graph.py`:

```python
import os

from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent
from dotenv import load_dotenv
from pathlib import Path

AGENT_DIR = Path(__file__).parent.parent

load_dotenv(AGENT_DIR / ".env")

from novo_agent.prompts import NOVO_AGENT_INSTRUCTIONS
from novo_agent.tools import nova_tool

model = init_chat_model("model-name", model_provider="openai", temperature=0.0)

graph = create_deep_agent(
    model=model,
    tools=[nova_tool],
    system_prompt=NOVO_AGENT_INSTRUCTIONS,
)
```

### Passo 3: Registrar no langgraph.json

Edite `langgraph.json` e adicione o novo graph:

```json
{
  "dependencies": ["."],
  "graphs": {
    "planning": "./src/agent/planning_graph.py:graph",
    "research": "./src/agent/research_graph.py:graph",
    "novo_agent": "./src/agent/novo_agent_graph.py:graph"
  },
  "env": ".env",
  "http": {
    "app": "./src/agent/webapp.py:app",
    "cors": {
      "allow_origins": ["*"],
      "allow_methods": ["*"],
      "allow_headers": ["*"],
      "allow_credentials": true
    }
  }
}
```

### Passo 4: Reiniciar o servidor

```bash
langgraph dev --port 8101 --no-browser
```

## Endpoints Disponíveis

### Threads

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/threads` | Criar thread |
| GET | `/threads` | Listar threads |
| GET | `/threads/{thread_id}` | Obter thread |
| DELETE | `/threads/{thread_id}` | Deletar thread |
| GET | `/threads/{thread_id}/state` | Obter estado |
| PUT | `/threads/{thread_id}/state` | Atualizar estado |

### Runs

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/threads/{thread_id}/runs` | Executar agente |
| POST | `/assistants/{assistant_id}/runs/stream` | Streaming |

### Assistentes

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/assistants` | Listar assistentes |
| POST | `/assistants/search` | Buscar assistente |
| GET | `/assistants/{assistant_id}` | Obter assistente |

### Custom

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Health check |
| GET | `/agents` | Listar agentes disponíveis |

## Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DATABASE_URL` | URL de conexão PostgreSQL | `postgresql://agent_user:password123@localhost:5432/deepagents` |
| `POSTGRES_URI` | URI PostgreSQL para persistência LangGraph | `postgresql://agent_user:password123@localhost:5432/deepagents` |
| `OPENAI_API_KEY` | API Key OpenAI | - |
| `OPENAI_API_BASE` | Endpoint alternativo OpenAI | - |
| `TAVILY_API_KEY` | API Key Tavily | - |
| `BDC_BASE_URL` | URL da JP BDC API | `http://localhost:8100` |
| `BDC_PASSKEY` | Passkey para autenticação JP BDC | - |

## Troubleshooting

### "ModuleNotFoundError"

Certifique-se de que:
1. O ambiente virtual está ativo: `source .venv/bin/activate`
2. O pyproject.toml inclui o novo pacote em `[tool.setuptools].packages`

### Persistência não funciona

1. Verifique se `POSTGRES_URI` está no `.env`
2. Teste a conexão: `psql $POSTGRES_URI -c "SELECT 1"`

### Porta em uso

```bash
# Verificar processo na porta
lsof -i :8101

# Matar processo
kill <PID>
```
