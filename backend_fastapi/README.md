# Backend FastAPI - Deep Agents

Backend alternativo em FastAPI para os agentes Deep Agents, compatível com o SDK LangGraph.

## Propósito

Este backend foi criado para testar e isolar problemas de consumo de memória do LangGraph API original. Permite comunicação direta com os agentes existentes (`planning`, `research`, `simple`)sem a sobrecarga do LangGraph Server.

## Diferenças do LangGraph Original

| Característica | LangGraph API (8101) | FastAPI Backend (8102) |
|----------------|---------------------|------------------------|
| Servidor | LangGraph SDK Server | FastAPI customizado |
| Persistência | PostgreSQL | In-memory (memória) |
| Threads | Persistidas em DB | Apenas em memória |
| Streams | LangGraph native | SSE (sse-starlette) |
| Recursos | Full-featured | Mínimo (threads + runs) |

## Quick Start

```bash
# Ativar virtualenv
source .venv/bin/activate

# Rodar o servidor
cd backend_fasapi
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../agents_and_backend/src"
uvicorn main:app --host 0.0.0.0 --port 8102

# Ou usar o script
./run.sh
```

## Endpoints

### Health

```bash
GET /health
```

Resposta:
```json
{"status": "ok", "backend": "fastapi"}
```

### Assistantes

```bash
GET /assistants
```

Resposta:
```json
[
  {
    "assistant_id": "planning",
    "graph_id": "planning",
    "name": "Planning Agent",
    "description": "Strategic planning agent with project and task management",
    "config": {}
  },
  {
    "assistant_id": "research",
    "graph_id": "research",
    "name": "Research Agent",
    "description": "Deep research agent with sub-agent delegation",
    "config": {}
  },
  {
    "assistant_id": "simple",
    "graph_id": "simple",
    "name": "Simple Agent",
    "description": "Simple agent with basic arithmetic tools",
    "config": {}
  }
]
```

### Threads

#### Criar thread

```bash
POST /threads
```

Parâmetros opcionais:
- `metadata`: objeto com metadados

Resposta:
```json
{
  "thread_id": "uuid-aqui",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "metadata": {},
  "status": "idle",
  "values": {}
}
```

#### Listar threads

```bash
GET /threads?limit=20&offset=0&status=idle
```

#### Buscar threads

```bash
POST /threads/search
Content-Type: application/json

{
  "limit": 20,
  "offset": 0,
  "status": "idle",
  "metadata": {"graph_id": "planning"}
}
```

#### Obter thread

```bash
GET /threads/{thread_id}
```

#### Atualizar thread

```bash
PATCH /threads/{thread_id}
Content-Type: application/json

{
  "metadata": {"key": "value"}
}
```

### Estado da Thread

#### Obter estado

```bash
GET /threads/{thread_id}/state
```

#### Atualizar estado

```bash
POST /threads/{thread_id}/state
Content-Type: application/json

{
  "values": {"messages": [...]}
}
```

### Runs

#### Criar run

```bash
POST /threads/{thread_id}/runs
Content-Type: application/json

{
  "assistant_id": "planning",
  "input": {"messages": [{"type": "human", "content": "Hello"}]},
  "config": {}
}
```

#### Run síncrono (wait)

```bash
POST /threads/{thread_id}/runs/wait
Content-Type: application/json

{
  "assistant_id": "research",
  "input": {"messages": [{"type": "human", "content": "Pesquise sobre IA"}]}
}
```

#### Run stream

```bash
POST /threads/{thread_id}/runs/stream
Content-Type: application/json

{
  "assistant_id": "simple",
  "input": {"messages": [{"type": "human", "content": "Some math"}]}
}
```

Resposta: Stream SSE com eventos.

## Configuração

### Variáveis de Ambiente

Copie `.env` de `agents_and_backend`:

```bash
cp ../agents_and_backend/.env ./
```

Principais variáveis:
- `OPENAI_API_KEY` - API key para modelos
- `OPENAI_API_BASE` - Endpoint alternativo (openrouter)
- `TAVILY_API_KEY` - Para ferramenta de busca
- `BDC_BASE_URL` - API JP BDC
- `BDC_PASSKEY` - Passkey JP BDC

### PYTHONPATH

O backend precisa do caminho para os agentes:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../agents_and_backend/src"
```

## Estrutura do Projeto

```
backend_fasapi/
├── main.py              # App FastAPI + CORS
├── models.py            # Modelos Pydantic
├── storage.py           # Armazenamento em memória
├── routes/
│   ├── assistants.py    # /assistants
│   ├── threads.py       # /threads
│   └── runs.py          # /runs (execução agentes)
├── graphs/              # Diretório para graphs (reservado)
├── requirements.txt     # Dependências
├── .env                 # Variáveis de ambiente
└── run.sh               # Script de execução
```

## Integração com Frontend

No frontend, altere o `deploymentUrl`:

```typescript
// Antes (LangGraph)
const config = {
  deploymentUrl: "http://localhost:8101",
  assistantId: "planning",
};

// Depois (FastAPI)
const config = {
  deploymentUrl: "http://localhost:8102",
  assistantId: "planning",
};
```

O SDK `@langchain/langgraph-sdk` é compatível com este backend.

## Limitações

1. **Sem persistência**: Threads são perdidas ao reiniciar o servidor
2. **Sem checkpoints**: Histórico não é persistido
3. **Sem concurrent runs**: Uma thread por vez
4. **Carregamento dinâmico**: Graphs são carregados na inicialização

## Troubleshooting

### "API key is required"

Certifique-se que o arquivo `.env` está presente e as variáveis estão exportadas:

```bash
source ../agents_and_backend/.env
```

### Graph não carrega

Verifique os erros no console ao iniciar:

```bash
Failed to load research graph: API key is required. Set TAVILY_API_KEY...
```

Isso indica que as variáveis de ambiente não estão configuradas.

## Dependências

```
fastapi
uvicorn
pydantic
python-dotenv
sse-starlette
langgraph
deepagents
langchain-openai
httpx
```
