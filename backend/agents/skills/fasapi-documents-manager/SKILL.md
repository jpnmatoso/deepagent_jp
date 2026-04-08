---
name: fasapi-documents-manager
description: Especializado em gerenciar documentos da JP BDC API. Use quando o usuário precisar listar, criar, buscar, abrir, editar ou excluir documentos. Autenticação automática via BDC_PASSKEY.
---

# JP BDC Documents Manager

Skill para gerenciar documentos da JP BDC API usando a tool `documents_manager`.

## Ferramenta Disponivel

Use a tool **`documents_manager`** para todas as operacoes CRUD em documentos.

## Acoes Disponiveis

| Acao | Descricao | Parametros |
|------|-----------|------------|
| `list` | Lista ultimos 10 documentos publicados | `limit` (opcional), `project_id` |
| `get` | Abre/exibe documento completo | `doc_id` |
| `create` | Cria novo documento | `title`, `body` (obrig.), `tags`, `project_id`, `author`, `status`, `references` |
| `update` | Atualiza documento | `doc_id`, campos opcionais |
| `delete` | Remove documento | `doc_id` |
| `search` | Busca documentos | `query`, `project_id`, `status`, `limit` |

## Formato das Tags

Tags podem ser passadas de duas formas:

**1. Lista de strings (preferido):**
```
tags: ["api", "notas", "python"]
```

**2. String separada por virgulas (convertido automaticamente):**
```
tags: "api, notas, python"
```

Ambos formatos resultam em: `["api", "notas", "python"]`

## Comportamento Padrao

### list
- Retorna os ultimos 10 documentos com status `published`
- Use `project_id` para filtrar por projeto
- Use `search` para buscas mais especificas

### get
- Exibe o documento completo com todo o conteudo
- Inclui tags, referencias, autor e metadata

### create
- `title` e `body` sao obrigatorios
- `author` default: "agent"
- `status` default: "published"
- `tags` e `references` sao opcionais

### update
- `doc_id` e obrigatorio
- Campos nao fornecidos mantem valores atuais (busca documento existente automaticamente)
- Tags podem ser string ou lista
- Para mudar apenas o status, basta fornecer `doc_id` e `status`

**Exemplo - Mudar apenas status:**
```
action: "update"
doc_id: 217
status: "draft"
```

## Status Aceitos

| Entrada | API |
|---------|-----|
| `publicado`, `published` | `published` |
| `rascunho`, `draft` | `draft` |
| `arquivado`, `archived` | `archived` |

## Autenticacao

A autenticacao e **automatica** via `BDC_PASSKEY`.

## Exemplos

### Listar documentos recentes
```
action: "list"
```

### Listar docs de um projeto
```
action: "list"
project_id: 47
```

### Buscar documentos por termo
```
action: "search"
query: "arquitetura"
```

### Buscar docs de um projeto
```
action: "search"
query: "api"
project_id: 47
```

### Abrir/exibir documento
```
action: "get"
doc_id: 123
```

### Criar documento com tags (lista)
```
action: "create"
title: "Nota sobre API"
body: "Conteudo do documento..."
tags: ["api", "notas", "python"]
project_id: 47
```

### Criar documento com tags (string)
```
action: "create"
title: "Nota sobre API"
body: "Conteudo do documento..."
tags: "api, notas, python"
project_id: 47
```

### Editar apenas o status do documento
```
action: "update"
doc_id: 217
status: "draft"
```

### Editar documento completo
```
action: "update"
doc_id: 123
title: "Novo titulo"
body: "Novo conteudo..."
tags: "tag1, tag2"
status: "published"
```

### Editar tags do documento
```
action: "update"
doc_id: 123
tags: "nova-tag, tag-atualizada"
```

### Deletar documento
```
action: "delete"
doc_id: 123
```

## Triggers

Ativada quando usuario menciona:
- "documentos da JP BDC"
- "listar/buscar/criar/editar/deletar documentos"
- "abrir documento"
- "criar nota"
- "base de conhecimento"
- qualquer operacao CRUD em documentos
