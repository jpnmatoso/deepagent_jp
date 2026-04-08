---
name: sprint-planner
description: Especializado em planejamento de sprint. Use quando usuário disser "vamos fazer o planejamento", "planejar sprint", "sprint planning" ou variações. Auxilia a selecionar e mover tarefas para sprint.
---

# Sprint Planner

Skill para planejamento de tarefas da Sprint usando as tools `projects_manager` e `tasks_manager`.

## Fluxo de Trabalho

### Passo 1: Listar Projetos com Tarefas

1. Use `projects_manager` com `action: "list"` para listar todos os projetos
2. Ordene os projetos por ID (mais antigo primeiro - IDs menores para maiores)
3. Para cada projeto, verifique se há tarefas waiting usando `tasks_manager` com `action: "list"`, `project_id` e `status: "waiting"`
4. REMOVA da lista os projetos que NÃO possuem tarefas waiting
5. Se todos os projetos foram removidos, informe: "Todos os projetos já estão sem tarefas waiting. Sprint limpa!"
6. Mostre a lista numerada de projetos válidos ao usuário
7. Comece automaticamente pelo primeiro projeto da lista
8. Diga: "Iniciando pelo projeto [nome] (ID mais antigo)..." e vá direto para o Passo 2

### Passo 2: Selecionar Projeto

1. Aguarde usuário selecionar o projeto (por número ou nome)
2. Armazene o `project_id` selecionado
3. Use `tasks_manager` com `action: "list"`, `project_id` e `status: "waiting"` para listar tarefas waiting

### Passo 3: Ordenar e Mostrar Tarefas

1. Ordene as tarefas waiting por categoria:
   - **Urgente** (primeiro)
   - **Importante** (segundo)
   - **Circunstancial** (terceiro)

2. Formate a saída assim:
   ```
   Tarefas Waiting - Projeto [nome]:
   
   Urgente:
   [1] [id] Título da tarefa urgente
   [2] [id] Título da tarefa urgente 2
   
   Importante:
   [3] [id] Título da tarefa importante
   [4] [id] Título da tarefa importante 2
   
   Circunstancial:
   [5] [id] Título da tarefa circunstancial
   ```

### Passo 4: Aguardar Seleção do Usuário

1. Mostre as tarefas ordenadas
2. Pergunte: "Quais tarefas deseja mover para sprint? (digite os números separados por vírgula, ou 'nenhuma')"
3. Aguarde resposta

### Passo 5: Mover Tarefas para Sprint

Para cada tarefa selecionada:
1. Use `tasks_manager` com `action: "update"`, `task_id` e `status: "sprint"`
2. Confirme: "Tarefa '[título]' movida para sprint ✓"

### Passo 6: Próximo Projeto

1. Após mover tarefas, verifique se há mais projetos na lista
2. Se **sim**: Vá automaticamente para o próximo projeto (próximo ID)
   - Diga: "Próximo: [nome do próximo projeto]..."
   - Volte ao Passo 2
3. Se **não**: Mostre resumo final:
   ```
   Planejamento concluído!
   
   Projetos planejados: X
   Tarefas em sprint: Y
   ```

## Alias de Categorias

| Usuário diz | API espera |
|------------|------------|
| urgente, bug, critica | circumstantial (marca como 'urgent' se existir) |
| importante, medio, normal | circumstantial |
| circunstancial, baixa | circumstantial |

Se a API não tiver categoria específica, agrupe por similaridade no título.

## Comandos do Usuário

| Comando | Ação |
|---------|------|
| "pular" | Pula para o próximo projeto automaticamente |
| "pular [nome]" | Pula para projeto específico |
| "nenhuma" | Não move tarefas desse projeto |
| "resumo", "resumo final" | Mostra estatísticas do planejamento |
| "sair", "terminar" | Encerra planejamento e mostra resumo final |

## Resumo Visual da Sprint

Ao encerrar o planejamento, gere um resumo visual completo:

1. Use `tasks_manager` com `action: "sprint"` para listar todas as tarefas em sprint
2. Use `projects_manager` com `action: "list"` para ter nomes dos projetos
3. Crie um mapa de project_id → nome do projeto
4. Agrupe as tarefas sprint por projeto
5. Mostre o resumo assim:

```
╔══════════════════════════════════════════════════════════════╗
║                    SPRINT PLANNING CONCLUÍDO                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📊 RESUMO                                                   ║
║  ─────────────────────────────────────────────────────────   ║
║  Total de tarefas em sprint: X                               ║
║  Projetos afetados: Y                                        ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📋 TAREFAS POR PROJETO                                      ║
║  ─────────────────────────────────────────────────────────   ║
║                                                              ║
║  [Nome do Projeto 1] (Z tarefas)                             ║
║  ├── [id] Título da tarefa 1                                 ║
║  ├── [id] Título da tarefa 2                                 ║
║  └── [id] Título da tarefa 3                                 ║
║                                                              ║
║  [Nome do Projeto 2] (W tarefas)                             ║
║  ├── [id] Título da tarefa 1                                 ║
║  └── [id] Título da tarefa 2                                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

## Dicas

- Use `tasks_manager` com `action: "search"` para buscar tarefas por termo se necessário
- Mantenha contexto do projeto atual durante todo o fluxo
- Se não houver tarefas waiting, informe e prossiga para próximo projeto
- Count: "sem tarefas waiting" é uma resposta válida

## Triggers

Ativada quando usuário menciona:
- "fazer o planejamento"
- "planejar sprint"
- "sprint planning"
- "planejar tarefas"
- "vamos planejar"
- "iniciar planejamento"
