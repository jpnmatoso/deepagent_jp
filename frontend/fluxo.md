# Fluxo de Mensagens no Frontend

## 1. Novo chat (threadId = null)
- `useStream` monta, `fetchStateHistory: true` mas **não faz chamada API** (threadId é null)
- `stream.messages = []`

## 2. Usuário envia "Olá."
- `sendMessage()` cria `{ id: uuid, type: "human", content: "Olá." }`
- **Update otimista**: mensagem humana aparece imediatamente na UI
- `POST /threads` → cria thread
- `POST /threads/{id}/runs/stream` → inicia SSE com `streamMode: ["messages-tuple", "values"]`

## 3. Durante streaming
- Eventos `messages` → `MessageTupleManager` acumula chunks por ID
- Eventos `values` → **substituem TODO o estado** (`this.setStreamValues(data)`)
- Mensagens aparecem na UI

## 4. Stream completa
- `onSuccess()` chama `history.mutate(threadId)` → `POST /threads/{id}/history`
- `stream.values` é setado para `null`
- **`stream.messages` agora vem de `historyValues`** (do history endpoint)
- Se `historyValues` estiver vazio → **mensagens desaparecem**

---

## Causa mais provável do problema

O **ponto crítico** é o passo 4. Após o stream completar, o SDK refaz a busca do history e usa `threadHead.values.messages` como fonte de verdade. Se o history endpoint retornar `values.messages` vazio ou mal formatado, as mensagens somem.

### Problemas identificados e corrigidos

1. **`POST /history` lia `limit` como query param** — o SDK envia no body JSON → endpoint retornava limite errado
2. **Mensagens sem `id`** — o SDK ignora mensagens sem ID (`console.warn("No message ID found")`)
3. **`next_nodes` calculado errado** — quebrava a árvore de checkpoints do SDK
4. **Checkpoint inicial não salvava a mensagem humana** — history começava vazio
5. **Metadata faltando campos** — `run_id`, `user_id`, `created_by`, etc.

---

## Diagrama do Fluxo

```
1. Page loads
   └─ threadId = null (URL query param)
   └─ useStream mounts: history fetch short-circuits (threadId is null)
   └─ stream.messages = []

2. User types + sends "Hello"
   └─ sendMessage() creates { id: uuid, type: "human", content: "Hello" }
   └─ stream.submit({ messages: [humanMsg] }, { optimisticValues: ... })

3. Optimistic update
   └─ stream.values = { messages: [humanMsg] }
   └─ UI renders human message immediately

4. Thread creation
   └─ POST /threads  →  returns { thread_id: "abc-123" }
   └─ onThreadId("abc-123") updates URL
   └─ onCreated callback fires → onHistoryRevalidate()

5. Stream run
   └─ POST /threads/abc-123/runs/stream  (streamMode: ["messages-tuple", "values"])
   └─ SSE events arrive:
       ├─ "messages" events → MessageTupleManager accumulates chunks by ID
       │                     → messages[index] = toMessageDict(chunk)
       └─ "values" events   → replaces entire state object

6. Stream completes
   └─ onSuccess() calls history.mutate(threadId)
   └─ POST /threads/abc-123/history  (limit: 10)
   └─ branchContext computed from history
   └─ stream.values set to null → falls through to historyValues
   └─ isLoading = false
   └─ onFinish callback fires → onHistoryRevalidate()

7. UI now reads messages from historyValues (fresh from history endpoint)
```

---

## Por que as mensagens desaparecem

O SDK `useStream` funciona em duas fases:

### Fase 1: Durante streaming
- `stream.messages` vem de `stream.values` (setado por eventos SSE)
- Mensagens aparecem normalmente

### Fase 2: Após streaming completar
- `onSuccess()` refaz `POST /threads/{id}/history`
- `stream.values` é limpo (`null`)
- `stream.messages` passa a vir de `historyValues` = `threadHead.values.messages`
- **Se `historyValues.messages` for `[]` → tela limpa**

### O que pode causar `historyValues.messages = []`

1. History endpoint retorna `values.messages` vazio
2. History endpoint retorna `values` sem a chave `messages`
3. `threadHead` é `undefined` (history vazio ou mal formatado)
4. `getMessages({})` retorna `[]` quando `values.messages` não é array
5. `RemoveMessage` events removem mensagens do array
