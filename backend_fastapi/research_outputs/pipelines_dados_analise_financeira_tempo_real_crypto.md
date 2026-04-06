# Pipelines de Dados para Análise Financeira em Tempo Real: Foco em Criptomoedas

**Data da Pesquisa:** 6 de abril de 2026
**Escopo:** Arquiteturas, ferramentas, processamento, armazenamento, orquestração e monitoramento para pipelines de baixa latência

---

## Sumário Executivo

Este relatório apresenta uma análise abrangente de pipelines de dados para análise financeira em tempo real, com foco específico em criptomoedas e requisitos de baixa latência. A pesquisa identificou arquiteturas modernas que conseguem atingir latências de sub-500ms end-to-end, ferramentas otimizadas para streaming financeiro, e práticas de engenharia validadas por empresas líderes como Coinbase, Binance e outras.

**Principais descobertas:**
- Latências de 180-500ms são alcançáveis com arquiteturas streaming bem projetadas
- Redis Streams oferece sub-millisecond latency para volumes moderados (<1TB/dia)
- Apache Spark Real-Time Mode atinge sub-100ms com escalabilidade enterprise
- TimescaleDB se destaca como solução time-series com SQL nativo
- Monitoramento com Prometheus + Grafana é padrão do setor

---

## 1. Arquiteturas de Pipeline: Batch vs Streaming

### 1.1 Comparação Fundamental

| Característica | Batch Processing | Stream Processing |
|----------------|------------------|-------------------|
| **Latência** | Segundos a horas | Milissegundos a segundos |
| **Throughput** | Alto (volume concentrado) | Variável (contínuo) |
| **Complexidade** | Menor | Maior |
| **Custo** | Previsível | Pode ser maior (24/7) |
| **Casos de Uso** | Relatórios históricos, ETL | Trading, detecção de fraude, monitoramento |

### 1.2 Quando Usar Cada Abordagem

**Batch Processing é ideal para:**
- Processamento de grandes volumes históricos
- Relatórios diários/semanais
- ETL tradicional para data warehouses
- Análises que não requerem latência <1 minuto

**Stream Processing é essencial para:**
- Análise de criptomoedas e trading algorítmico
- Detecção de fraude em tempo real
- Monitoramento de mercado com latência <500ms
- Aplicações que precisam reagir a eventos em milissegundos

### 1.3 Arquitetura Híbrida Moderna

A tendência atual é usar **Lambda Architecture** ou **Kappa Architecture**:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Batch Layer    │    │  Speed Layer     │    │  Serving Layer  │
│  (Horas/Dias)   │◄──►│  (Segundos)      │◄──►│  (Consultas)    │
│                 │    │                  │    │                 │
│ • Processamento │    │ • Stream         │    │ • API           │
│   histórico     │    │ • Baixa latência │    │ • Dashboards    │
│ • Corrige erros  │    │ • Dados brutos   │    │ • Alertas       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## 2. Ferramentas de Streaming

### 2.1 Apache Kafka vs Redis Streams

#### Apache Kafka

**Vantagens:**
- Escalabilidade horizontal massiva (100K+ msgs/seg)
- Retenção de longo prazo (dias a anos)
- Replicação e tolerância a falhes robustas
- Ecossistema rico (Kafka Connect, ksqlDB, etc.)
- Usado por Coinbase para processamento de risco

**Desvantagens:**
- Latência mais alta (10-100ms típico)
- Complexidade operacional (ZooKeeper, múltiplos brokers)
- Overhead de recursos significativo

**Melhor para:** Volumes >1TB/dia, múltiplos consumidores, retenção prolongada

#### Redis Streams

**Vantagens:**
- Latência sub-millisecond
- Simplicidade operacional (único container)
- Consumer groups nativos
- Baixo overhead de recursos
- Ideal para <5.000 msgs/seg

**Desvantagens:**
- Limitado por memória RAM
- Retenção mais curta (horas a dias)
- Escalabilidade limitada comparada a Kafka

**Melhor para:** Baixa latência (<1ms), volumes moderados, operação simplificada

**Caso Prático:** O repositório `crypto-realtime-analytics-pipeline` usa Redis Streams e atinge <500ms end-to-end com 1.400 msgs/seg [1].

#### Comparação de Performance

| Métrica | Redis Streams | Apache Kafka |
|---------|---------------|--------------|
| Latência p50 | <1ms | 10-50ms |
| Throughput | ~8.000 msgs/seg | 100K+ msgs/seg |
| Retenção | Horas-dias | Dias-anos |
| Complexidade | Baixa | Alta |
| Custo operacional | Baixo | Alto |

### 2.2 Apache Spark Structured Streaming - Real-Time Mode

**Revolução em 2025:** O Databricks anunciou o **Real-Time Mode (RTM)** para Spark Structured Streaming, trazendo latência sub-100ms para o ecossistema Spark [2].

**Inovações técnicas:**
1. **Fluxo contínuo:** Processa eventos individualmente, não em microbatches
2. **Pipeline scheduling:** Estágios rodam simultaneamente sem bloqueio
3. **Streaming shuffle:** Dados passam entre tarefas imediatamente

**Performance comparada:**
- Benchmark contra Apache Flink: Spark RTM até 92% mais rápido
- Coinbase: Redução de 80%+ na latência, atingindo sub-100ms p99
- DraftKings: Latência ultra-baixa para detecção de fraude em betting

**Vantagens do Spark RTM:**
- Mesma API para batch e streaming (evita duplicação de código)
- Escalabilidade horizontal
- Integração nativa com Delta Lake
- Ecossistema maduro (MLlib, GraphX, etc.)

**Código de exemplo:**
```python
# Habilitar Real-Time Mode
spark.conf.set("spark.sql.streaming.minBatchesToRetain", "1")
spark.conf.set("spark.sql.streaming.stateStore.providerClass", 
               "org.apache.spark.sql.execution.streaming.state.RocksDBStateStoreProvider")

# Streaming query com trigger contínuo
query = df.writeStream \
    .format("delta") \
    .trigger(processingTime="0 seconds") \
    .start()
```

### 2.3 Apache Airflow para Orquestração

**Estado em 2025:** Airflow domina o mercado de orquestração de workflows com crescimento exponencial [3]:
- 31M de downloads mensais (vs 900K em 2020)
- 3K+ contribuidores
- 77K organizações usando

**Casos de uso em criptomoedas:**
- Orquestração de ETLs para dados históricos
- Agendamento de retreinamento de modelos ML
- Pipelines de backtesting
- Automação de relatórios de risco

**Recursos relevantes:**
- **Airflow 3 (abril 2025):** Versionamento de DAGs, UI modernizada, execução remota
- **MLOps:** 21.4% dos usuários usam para machine learning
- **GenAI:** 8.2% usam para generative AI (crescimento esperado)

**Melhores práticas:**
- Usar Kubernetes Operator para escalabilidade
- Implementar sensors para dependências externas
- Configurar alertas via Slack/Email
- Versionar DAGs com Git

---

## 3. Processamento de Dados em Tempo Real

### 3.1 Padrões de Processamento

**Window Operations:**
```python
# Exemplo: Janela deslizante de 1 minuto
windowed_stream = stream \
    .window("TUMBLING", "1 minute") \
    .groupBy("symbol") \
    .agg(
        avg("price").alias("avg_price"),
        sum("volume").alias("total_volume"),
        count("*").alias("trade_count")
    )
```

**Stateful Processing:**
- Manutenção de estado entre eventos (ex: médias móveis)
- Uso de `transformWithState` no Spark RTM
- Checkpointing para recuperação de falhas

### 3.2 Indicadores Técnicos em Tempo Real

**Implementação típica (do caso prático analisado):**

1. **SMA (Simple Moving Average):** Média dos últimos N preços
2. **EMA (Exponential Moving Average):** Média exponencial com pesos decrescentes
3. **RSI (Relative Strength Index):** Oscilador de momentum (0-100)
4. **VWAP (Volume Weighted Average Price):** Preço médio ponderado por volume
5. **Bollinger Bands:** SMA ± 2 desvios padrão
6. **Price Velocity:** Taxa de mudança de preço por segundo
7. **Volume Spike Detection:** Identificação de volume anormal

**Performance:** Todos os 7 indicadores calculados em <1ms por símbolo usando NumPy/Pandas vetorizados.

### 3.3 Otimizações de Latência

**Técnicas comprovadas:**
- **Batch processing de mensagens:** Processar 10-100 mensagens por batch
- **In-memory state:** Manter janelas rolantes na memória
- **Async I/O:** Usar asyncio/FastAPI para não bloquear
- **Connection pooling:** Reutilizar conexões DB
- **Compressão:** Snappy/LZ4 para dados em trânsito

---

## 4. Armazenamento Time-Series

### 4.1 Comparação: InfluxDB vs TimescaleDB vs PostgreSQL

#### InfluxDB

**Pontos fortes:**
- Engine customizada para time-series (TSM)
- Compressão até 100x
- Throughput de escrita: 250K-750K rows/seg
- Query language Flux poderosa para agregações temporais
- Retenção automática e downsampling

**Pontos fracos:**
- Suporte limitado a joins complexos
- ACID limitado
- Cluster aberto limitado (enterprise pago)
- Curva de aprendizado do Flux

**Melhor para:** Observability pura, IoT, métricas de infraestrutura

#### TimescaleDB

**Pontos fortes:**
- Extensão do PostgreSQL (herda todas as capacidades)
- Hypertables com particionamento automático
- Compressão 10-20x
- Continuous aggregates (materialized views auto-atualizadas)
- SQL completo + funções time-series
- Throughput: 100K-300K rows/seg

**Pontos fracos:**
- Requer PostgreSQL (overhead adicional)
- Licença enterprise para algumas features
- Menor throughput puro que InfluxDB

**Melhor para:** Aplicações que misturam dados relacionais + time-series (fintech, IoT com metadados)

#### PostgreSQL (nativo)

**Pontos fortes:**
- ACID completo, transações robustas
- Ecossistema maduro (18+ anos)
- Maior talent pool disponível
- Extensões (PostGIS, pg_partman, etc.)
- Custo total de propriedade mais baixo

**Pontos fracos:**
- Performance time-series inferior sem extensões
- Particionamento manual necessário
- Sem continuous aggregates nativas

**Melhor para:** Aplicações transacionais com necessidade de time-series secundária

### 4.2 Recomendação para Criptomoedas

**TimescaleDB é a escolha ideal** porque:
1. **SQL nativo:** Facilita consultas complexas (joins com tabelas de símbolos, alerts, etc.)
2. **Continuous aggregates:** Candles de 1m/5m/1h pré-computados automaticamente
3. **Compressão automática:** Reduz custos de storage em 90%+ após 7 dias
4. **Herda PostgreSQL:** ACID, indexes, ferramentas de backup, pool de conexões
5. **Custo:** Community edition gratuito com features completas

**Exemplo de schema:**
```sql
-- Hypertable para ticks brutos
CREATE TABLE raw_ticks (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    price DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    trade_id BIGINT
);
SELECT create_hypertable('raw_ticks', 'time', chunk_time_interval => INTERVAL '1 day');

-- Continuous aggregate para candles de 5 minutos
CREATE MATERIALIZED VIEW candles_5m
WITH (timescaledb.continuous) AS
SELECT time_bucket('5 minutes', time) AS bucket,
       symbol,
       first(price, time) AS open,
       last(price, time) AS close,
       max(price) AS high,
       min(price) AS low,
       sum(volume) AS volume
FROM raw_ticks
GROUP BY bucket, symbol;
```

---

## 5. Orquestração de Workflows

### 5.1 Apache Airflow - Estado da Arte 2025

**Crescimento explosivo:**
- 31M downloads/mês (35x crescimento desde 2020)
- 53.8% de enterprises com 50K+ employees usam para workloads críticos
- 20%+ das enterprises rodam 20+ instâncias de produção

**Tendências 2025:**
1. **AI/ML Ops:** 21.4% usam para MLOps, 8.2% para GenAI
2. **Multi-cloud:** 64.4% usam Python, Bash, Kubernetes operators para flexibilidade
3. **Revenue-generating:** 85% esperam aumentar soluções externas/geradoras de receita

**Airflow 3 (abril 2025):**
- Versionamento de DAGs
- UI modernizada
- Remote execution
- Event-driven scheduling

### 5.2 Alternativas Modernas

**Prefect:**
- Python-first
- Dynamic workflows
- Cloud-native

**Dagster:**
- Data-aware orchestration
- Asset-centric
- Type system robusto

**Mage:**
- Visual development + código
- Kafka nativo
- Foco em streaming

**Quando usar Airflow:**
- Workflows complexos com muitas dependências
- Necessidade de scheduling sofisticado
- Equipe já familiarizada
- Integração com ecossistema Hadoop/Spark

---

## 6. Monitoramento e Observabilidade

### 6.1 Stack Padrão: Prometheus + Grafana

**Por que é o padrão:**
- Pull-based metrics (simples de implementar)
- Query language poderosa (PromQL)
- Alertmanager integrado
- Ecossistema rico de exporters
- Grafana para visualização rica

**Métricas críticas para pipelines financeiros:**

| Categoria | Métrica | Threshold Recomendado |
|-----------|---------|----------------------|
| **Latência** | End-to-end latency p95 | <500ms |
| | Processing latency p99 | <100ms |
| | API response time p95 | <100ms |
| **Throughput** | Messages/sec | Monitorar tendência |
| | DB writes/sec | <80% da capacidade |
| **Erros** | Error rate | <0.1% |
| | Consumer lag | <1000 mensagens |
| **Recursos** | CPU usage | <70% |
| | Memory usage | <80% |
| | Disk I/O | <80% |

### 6.2 Alertas Críticos

**Alertas de Negócio:**
- Latência end-to-end >500ms por 5 min
- Consumer lag >10.000 mensagens
- API error rate >1%
- Conexão com exchange perdida (>60s)

**Alertas de Infraestrutura:**
- CPU >85% por 10 min
- Memória >90%
- Disco >85% cheio
- DB connections pool esgotado

### 6.3 Implementação Prática

**Exemplo de métricas customizadas (Python):**
```python
from prometheus_client import Counter, Histogram, Gauge

# Métricas
messages_received = Counter('crypto_messages_total', 'Total messages received', ['symbol'])
processing_latency = Histogram('crypto_processing_seconds', 'Processing latency')
db_write_latency = Histogram('crypto_db_write_seconds', 'DB write latency')
stream_length = Gauge('crypto_stream_length', 'Redis stream length', ['stream'])
ws_connections = Gauge('crypto_ws_connections', 'Active WebSocket connections')

# Uso
with processing_latency.time():
    result = process_message(msg)
messages_received.labels(symbol=msg['symbol']).inc()
```

**Dashboard Grafana pré-construído:**
- Latência end-to-end (p50, p95, p99)
- Throughput por símbolo
- Backlog do Redis Stream
- Conexões WebSocket ativas
- Taxa de erro da API
- Latência de escrita no DB

---

## 7. Casos de Uso e Exemplos Práticos

### 7.1 Pipeline de Criptomoedas com Redis Streams

**Repositório de referência:** `Hussein1055/crypto-realtime-analytics-pipeline` [1]

**Arquitetura:**
```
Coinbase WebSocket → Ingestion Service → Redis Streams → Processing Workers → TimescaleDB
                                                                      ↓
                                                                 FastAPI + React Dashboard
```

**Tech Stack:**
- **Ingestão:** Python asyncio + websockets
- **Message Queue:** Redis Streams (consumer groups)
- **Processamento:** Python + NumPy/Pandas
- **Storage:** TimescaleDB (hypertables + continuous aggregates)
- **API:** FastAPI (async + WebSocket)
- **Frontend:** React 18 + Recharts
- **Monitoramento:** Prometheus + Grafana
- **Containerização:** Docker Compose

**Performance:**
- Latência end-to-end: ~180ms (p50), ~340ms (p95)
- Throughput: ~1.400 msgs/seg (single worker)
- API response: ~18ms (p50), ~52ms (p95)
- DB write: ~2.800 rows/seg

**Indicadores implementados:**
- SMA (20, 50, 200 períodos)
- EMA (12, 26 períodos)
- RSI (14 períodos)
- VWAP (reset diário)
- Bollinger Bands (±2σ)
- Price Velocity
- Volume Spike Detection

### 7.2 Pipeline com Apache Kafka + Spark RTM

**Inspirado no caso Coinbase** [2]:

**Arquitetura:**
```
Binance/Kraken WebSocket → Kafka Producer → Kafka Topics → Spark RTM → Delta Lake → Serving Layer
```

**Características:**
- Kafka para alta throughput e replay
- Spark Real-Time Mode para sub-100ms
- Delta Lake para ACID e versionamento
- ML features computation inline

**Performance Coinbase:**
- Redução de 80%+ na latência
- Sub-100ms p99
- 250+ ML features computadas em tempo real
- Processamento de milhões de eventos/dia

### 7.3 Pipeline Híbrido: Batch + Streaming

**Padrão Lambda/Kappa:**

**Speed Layer (Streaming):**
- Kafka/Redis Streams
- Processamento em <1s
- Stateful window operations
- Resultados em tabelas "hot"

**Batch Layer:**
- Airflow + Spark batch
- Processamento histórico (dias/meses)
- Correção de dados
- Recalibração de modelos

**Serving Layer:**
- API unificada (consulta speed + batch)
- Materialized views
- Cache layer (Redis)

---

## 8. Melhores Práticas e Lições Aprendidas

### 8.1 Design para Baixa Latência

1. **Minimizar serialização:** Usar formatos binários (Avro, Protobuf) em vez de JSON
2. **Batch inteligente:** Tamanhos de batch de 10-100 mensagens (trade-off latency/throughput)
3. **In-memory processing:** Manter state na memória, não em disco
4. **Async throughout:** From ingestion to API response
5. **Connection pooling:** Reutilizar conexões DB e Redis
6. **Indexação apropriada:** TimescaleDB hypertables + índices compostos

### 8.2 Confiabilidade

1. **Exactly-once semantics:** Idempotent processing + deduplication
2. **Dead letter queues:** Isolar mensagens problemáticas
3. **Checkpointing:** State checkpoint a cada N segundos
4. **Retry com backoff:** Exponential backoff para falhas transitórias
5. **Circuit breakers:** Parar processamento se downstream falha

### 8.3 Observabilidade

1. **Correlation IDs:** Rastrear request através de todo o pipeline
2. **Structured logging:** JSON logs com contexto
3. **Metrics em todos os estágios:** Latência, throughput, erros
4. **Tracing distribuído:** OpenTelemetry para debugging
5. **Alertas proativos:** Não apenas reativos

### 8.4 Escalabilidade

1. **Partitioning por símbolo:** Kafka topics/partitions por símbolo
2. **Consumer groups paralelos:** Escalar workers horizontalmente
3. **Stateless onde possível:** Facilitar scaling
4. **State sharding:** Distribuir state por chave (símbolo)
5. **Backpressure handling:** Parar ingestion se processing laga

---

## 9. Stack Tecnológica Recomendada

### 9.1 Para Startups/Projetos Pequenos (<10 símbolos, <1K msgs/seg)

```
WebSocket (Coinbase/Binance) → Redis Streams → Python Workers → TimescaleDB → FastAPI → React
```

**Vantagens:**
- Simplicidade operacional (tudo em Docker Compose)
- Custo baixo (open source)
- Latência <500ms
- Fácil de entender e modificar

### 9.2 Para Empresas Médias (10-100 símbolos, 10K msgs/seg)

```
WebSocket → Kafka → Spark RTM → Delta Lake → API Layer → Dashboard
```

**Vantagens:**
- Escalabilidade horizontal
- Replayabilidade (Kafka retention)
- Processamento ML integrado
- Suporte a múltiplas exchanges

### 9.3 Para Enterprises (100+ símbolos, 100K+ msgs/seg)

```
Multi-Exchange → Kafka Cluster → Spark RTM Cluster → Data Lakehouse (Delta/Iceberg)
                    ↓                              ↓
               Flink (opcional)              Feature Store
                    ↓                              ↓
               Real-time ML                Serving Layer
```

**Vantagens:**
- Máxima escalabilidade
- Alta disponibilidade
- Suporte a múltiplas regiões
- Integração com data mesh

---

## 10. Considerações de Custo

### 10.1 Custos de Infraestrutura (Estimativa Mensal AWS)

| Componente | Pequeno | Médio | Grande |
|------------|---------|-------|--------|
| **Compute** | $200-500 | $1.000-5.000 | $10.000+ |
| **Kafka/Redis** | $100-300 | $500-2.000 | $3.000+ |
| **Database** | $100-300 | $500-1.500 | $2.000+ |
| **Storage** | $50-100 | $200-500 | $1.000+ |
| **Monitoring** | $0-50 | $100-300 | $500+ |
| **Total** | **$450-1.200** | **$2.300-9.300** | **$16.500+** |

### 10.2 Otimização de Custos

1. **Spot instances** para workers não-críticos
2. **Auto-scaling** baseado em load
3. **Data retention policies:** 7 dias hot, 30 days warm, archive cold
4. **Compressão:** TimescaleDB compression reduz storage 90%
5. **Reserved instances** para DBs e Kafka (1-3 anos)

---

## 11. Tendências Futuras (2026+)

### 11.1 AI/ML Integration

- **Feature stores online:** Materialized features para modelos em tempo real
- **Anomaly detection automática:** AutoML para detecção de padrões anormais
- **Predictive analytics:** Previsão de preços com modelos leves (online learning)

### 11.2 Multi-Exchange Aggregation

- Unificação de dados de múltiplas exchanges
- Arbitragem automática
- Market making algorithms

### 11.3 Serverless Streaming

- AWS Lambda/Kafka integration
- Pay-per-use computing
- Auto-scaling instantâneo

### 11.4 Edge Computing

- Processamento mais próximo da fonte
- Latência ainda menor (<10ms)
- Redução de bandwidth

---

## 12. Conclusões e Recomendações

### 12.1 Resumo Executivo

Para pipelines de análise de criptomoedas com baixa latência:

1. **Comece simples:** Redis Streams + TimescaleDB + FastAPI para MVP (<500ms)
2. **Escale com Kafka:** Quando throughput >10K msgs/seg ou necessidade de replay
3. **Use Spark RTM:** Para processamento complexo + ML features (Coinbase usa)
4. **Orquestre com Airflow:** Para ETLs batch e retreinamento de modelos
5. **Monitore tudo:** Prometheus + Grafana com alertas proativos

### 12.2 Checklist de Implementação

**Fase 1 - MVP (2-4 semanas):**
- [ ] Ingestão WebSocket (1 exchange)
- [ ] Redis Streams como buffer
- [ ] 3-5 indicadores técnicos básicos
- [ ] TimescaleDB com hypertables
- [ ] FastAPI REST + WebSocket
- [ ] Dashboard React simples
- [ ] Prometheus metrics básicos

**Fase 2 - Produção (4-8 semanas):**
- [ ] Múltiplas exchanges
- [ ] Todos os 7+ indicadores
- [ ] Alertas automáticos
- [ ] Grafana dashboard completo
- [ ] Testes de carga e stress
- [ ] CI/CD pipeline
- [ ] Documentação operacional

**Fase 3 - Escala (8+ semanas):**
- [ ] Migração para Kafka (se necessário)
- [ ] Spark RTM para processamento pesado
- [ ] Feature store para ML
- [ ] Multi-região deployment
- [ ] Disaster recovery
- [ ] Otimizações de custo

### 12.3 Lições Críticas

1. **Latência é relativa:** Sub-500ms é excelente para análise, mas trading algorítmico pode precisar <100ms
2. **Simplicidade primeiro:** Não over-engineer. Redis Streams resolve 80% dos casos
3. **Teste com dados reais:** Simulações não capturam latências reais de rede
4. **Monitoramento não é opcional:** Sem métricas, você está cego
5. **Planeje para falhas:** Tudo falha eventualmente. Designe para recuperação

---

## Fontes

[1] Hussein1055/crypto-realtime-analytics-pipeline. GitHub Repository. Disponível em: https://github.com/Hussein1055/crypto-realtime-analytics-pipeline

[2] Databricks. "Announcing General Availability of Real-Time Mode for Apache Spark Structured Streaming". Blog Databricks, 19 mar 2026. Disponível em: https://www.databricks.com/blog/announcing-general-availability-real-time-mode-apache-spark-structured-streaming-databricks

[3] Astronomer. "State of Airflow 2025: Unleashing the Future of Data Orchestration". Blog Astronomer, 27 fev 2025. Disponível em: https://www.astronomer.io/blog/state-of-airflow-2025-unleashing-the-future-of-data-orchestration/

[4] AutoMQ. "Apache Kafka vs. Redis Streams: Differences & Comparison". Blog AutoMQ, 5 abr 2025. Disponível em: https://www.automq.com/blog/apache-kafka-vs-redis-streams-differences-and-comparison

[5] Index.dev. "InfluxDB vs PostgreSQL vs TimescaleDB: Database Comparison 2026". Disponível em: https://www.index.dev/skill-vs-skill/database-timescaledb-vs-influxdb-vs-postgresql-time-series

[6] Mage AI. "Building real-time crypto trading pipelines with Kafka and Mage Pro". Blog Mage, 25 jun 2025. Disponível em: https://www.mage.ai/blog/building-real-time-crypto-trading-pipelines-with-kafka-and-mage-pro

[7] Huy Le. "Unlocking the Potential of Prometheus and Grafana: Key Use Cases". LinkedIn, 24 dez 2024. Disponível em: https://www.linkedin.com/pulse/unlocking-potential-prometheus-grafana-key-use-cases-huy-le-ze0pc

---

## Apêndices

### A. Exemplo de Código Completo (Producer)

```python
import asyncio
import websockets
from kafka import KafkaProducer
import json
import logging
from datetime import datetime

class CryptoProducer:
    def __init__(self, kafka_servers, topic):
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8'),
            acks='all',
            batch_size=16384,
            linger_ms=10
        )
        self.topic = topic
    
    async def stream_binance(self, symbols):
        streams = "/".join([f"{s}@trade" for s in symbols])
        url = f"wss://fstream.binance.com/stream?streams={streams}"
        
        async with websockets.connect(url) as ws:
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                trade = data.get('data', {})
                
                enriched = {
                    'symbol': trade.get('s'),
                    'price': float(trade.get('p', 0)),
                    'quantity': float(trade.get('q', 0)),
                    'timestamp': trade.get('T'),
                    'buyer_maker': trade.get('m'),
                    'trade_id': trade.get('t'),
                    'exchange': 'binance',
                    'processing_time': datetime.utcnow().isoformat()
                }
                
                self.producer.send(
                    topic=self.topic,
                    key=enriched['symbol'],
                    value=enriched
                )
```

### B. Exemplo de Schema TimescaleDB

```sql
-- Tabela principal de ticks
CREATE TABLE market_ticks (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8) NOT NULL,
    trade_id BIGINT,
    exchange VARCHAR(50),
    buyer_maker BOOLEAN
);
SELECT create_hypertable('market_ticks', 'time', 
                         chunk_time_interval => INTERVAL '1 day',
                         partitioning_column => 'symbol',
                         number_partitions => 4);

-- Índices compostos para queries comuns
CREATE INDEX idx_market_ticks_symbol_time ON market_ticks (symbol, time DESC);
CREATE INDEX idx_market_ticks_time ON market_ticks (time DESC);

-- Continuous aggregate para candles de 1 minuto
CREATE MATERIALIZED VIEW candles_1m
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 minute', time) AS bucket,
       symbol,
       first(price, time) AS open,
       last(price, time) AS close,
       max(price) AS high,
       min(price) AS low,
       sum(volume) AS volume,
       count(*) AS trade_count
FROM market_ticks
GROUP BY bucket, symbol;

-- Política de retenção (30 dias)
SELECT add_retention_policy('market_ticks', INTERVAL '30 days');
SELECT add_retention_policy('candles_1m', INTERVAL '90 days');
```

### C. Exemplo de Configuração Prometheus

```yaml
scrape_configs:
  - job_name: 'crypto-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
  
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:9121']
    scrape_interval: 30s
  
  - job_name: 'postgresql'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - "alerts.yml"
```

```yaml
# alerts.yml
groups:
  - name: crypto_pipeline
    rules:
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(crypto_processing_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Latência de processamento alta"
          description: "P95 latency > 500ms por 5 minutos"
      
      - alert: ConsumerLag
        expr: crypto_stream_length > 10000
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Backlog no Redis Stream"
          description: "Stream length > 10.000 mensagens"
```

---

**Fim do Relatório**

*Documento preparado por assistente de pesquisa em 6 de abril de 2026. Todas as informações foram coletadas de fontes públicas e referenciadas adequadamente.*