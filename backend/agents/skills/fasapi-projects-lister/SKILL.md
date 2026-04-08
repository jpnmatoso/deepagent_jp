---
name: fasapi-projects-lister
description: Especializado em gerenciar projetos da JP BDC API. Use quando o usuário precisar listar, criar, buscar, atualizar ou excluir projetos. Autenticação automática via BDC_PASSKEY.
---

# JP BDC Projects Manager

Skill para gerenciar projetos da JP BDC API usando a tool `projects_manager`.

## Ferramenta Disponivel

Use a tool **`projects_manager`** para todas as operacoes CRUD em projetos.

## Acoes Disponiveis

| Acao | Descricao | Parametros Necessarios |
|------|-----------|------------------------|
| `list` | Lista todos os projetos | `limit` (opcional, default: 50) |
| `create` | Cria novo projeto | `title` (obrigatorio), `body`, `status` |
| `get` | Obtem projeto especifico | `project_id` |
| `update` | Atualiza projeto existente | `project_id`, `title`/`body`/`status` |
| `delete` | Remove projeto | `project_id` |
| `search` | Busca projetos por termo | `query`, `limit` (opcional) |

## Autenticacao

A autenticacao e **automatica**. A tool usa a variavel de ambiente `BDC_PASSKEY` para fazer login automaticamente antes de cada requisicao.

**Nao faca chamadas HTTP manuais** - use sempre a tool `projects_manager`.

## Exemplos de Uso

### Listar projetos
```
action: "list"
limit: 20
```

### Buscar projetos
```
action: "search"
query: "projeto alpha"
limit: 10
```

### Criar projeto
```
action: "create"
title: "Novo Projeto"
body: "Descricao do projeto"
status: "active"
```

### Atualizar status do projeto
```
action: "update"
project_id: 47
status: "inactive"
```

### Obter detalhes de um projeto
```
action: "get"
project_id: 47
```

### Deletar projeto
```
action: "delete"
project_id: 47
```

## Observacoes

- Status aceitos: `active`, `inactive`, `archived`
- Alias em portugues sao aceitos: `ativo`/`inativo`
- O `project_id` e sempre um numero inteiro
- Responses incluem contagem de documentos e tarefas associadas

## Triggers

Ativada quando usuario menciona:
- "projetos da JP BDC"
- "listar/criar/atualizar/deletar projetos"
- "projetos do Sagitario"
- qualquer operacao CRUD em projetos
