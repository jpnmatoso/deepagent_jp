---
name: fasapi-tasks-manager
description: Especializado em gerenciar tarefas da JP BDC API. Use quando o usuário precisar listar, criar, buscar, atualizar ou excluir tarefas. Autenticação automática via BDC_PASSKEY.
---

# JP BDC Tasks Manager

Skill para gerenciar tarefas da JP BDC API usando a tool `tasks_manager`.

## Ferramenta Disponivel

Use a tool **`tasks_manager`** para todas as operacoes CRUD em tarefas.

## Acoes Disponiveis

| Acao | Descricao | Parametros |
|------|-----------|------------|
| `list` | Lista tarefas (sprint + waiting) | `limit`, `project_id`, `category` |
| `sprint` | Lista tarefas em sprint | `limit` |
| `create` | Cria nova tarefa | `title` (obrig.), `body`, `status`, `category`, `project_id` |
| `get` | Obtem tarefa especifica | `task_id` |
| `update` | Atualiza tarefa existente | `task_id`, campos opcionais |
| `delete` | Remove tarefa | `task_id` |
| `search` | Busca tarefas por termo | `query`, `limit`, `project_id` |

## Comportamento Padrao

### list
- Retorna apenas tarefas com status `sprint` ou `waiting`
- Nao mostra project_id para manter lista limpa
- Use `status` para filtrar um status especifico

### sprint
- Retorna apenas tarefas com status `sprint`
- Formato simplificado: `[id] titulo`

## Status de Tarefas

O status da tarefa define seu estado no fluxo de trabalho:

| Status | Significado | Alias aceitos |
|--------|-------------|---------------|
| `waiting` | Aguardando | "espera", "waiting" |
| `open` | Aberta/Em progresso | "aberta", "open" |
| `sprint` | Na sprint atual | "sprint" |
| `done` | Concluida com sucesso | "concluida", "concluído", "done", "feita" |
| `failure` | Falhou/Nao teve sucesso | "falha", "falhou", "failure", "insucesso", "failed" |

### Atualizar status

Para mudar APENAS o status da tarefa, basta fornecer `task_id` e `status`:

```
action: "update"
task_id: 123
status: "done"
```

**IMPORTANTE**: Nao e necessario fornecer title, body ou category - eles sao mantidos automaticamente.

## Autenticacao

A autenticacao e **automatica** via `BDC_PASSKEY`.

## Exemplos

### Listar tarefas (sprint + waiting)
```
action: "list"
project_id: 47
```

### Listar tarefas em sprint (formato simplificado)
```
action: "sprint"
```

### Filtrar apenas waiting
```
action: "list"
status: "waiting"
```

### Criar tarefa
```
action: "create"
title: "Implementar feature X"
status: "open"
project_id: 47
```

### Marcar tarefa como concluida
```
action: "update"
task_id: 123
status: "done"
```

### Mover tarefa para sprint
```
action: "update"
task_id: 123
status: "sprint"
```

### Mover tarefa para waiting
```
action: "update"
task_id: 123
status: "waiting"
```

### Marcar tarefa como falha
```
action: "update"
task_id: 123
status: "failure"
```

## Triggers

- "tarefas da JP BDC"
- "listar/criar/atualizar/deletar tarefas"
- "tarefas do projeto"
- "tarefas em sprint"
- qualquer operacao CRUD em tarefas
