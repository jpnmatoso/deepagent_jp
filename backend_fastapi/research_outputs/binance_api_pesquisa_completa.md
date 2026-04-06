# API da Binance: Guia Completo de Coleta de Dados de Pares USDT

**Data da Pesquisa:** 6 de abril de 2026

---

## 1. Introdução

A Binance oferece uma API robusta para coleta de dados de mercado, suportando tanto operações Spot quanto Futures. Esta pesquisa cobre endpoints essenciais para obtenção de dados históricos, tickers, order book e volume, além de rate limits, métodos de autenticação e exemplos práticos em Python [1][2].

---

## 2. Endpoints da API

### 2.1 API Spot (Binance.com)

**Base URL:** `https://api.binance.com`

#### Endpoints Principais:

**a) Klines/Candlesticks (Dados Históricos)**
```
GET /api/v3/klines
```
- **Peso (Weight):** 1
- **Parâmetros:**
  - `symbol` (STRING) - Obrigatório
  - `interval` (ENUM) - Obrigatório (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
  - `startTime` (LONG) - Opcional
  - `endTime` (LONG) - Opcional
  - `limit` (INT) - Opcional, padrão 500, máximo 1000
- **Fonte de dados:** Database
- **Retorno:** Array de arrays com [timestamp, open, high, low, close, volume, closeTime, quoteVolume, trades, takerBuyBaseVolume, takerBuyQuoteVolume, ignore] [1]

**b) Tickers - 24hr Statistics**
```
GET /api/v3/ticker/24hr
```
- **Peso:** 1-40 dependendo do número de símbolos
- **Parâmetros:**
  - `symbol` (STRING) - Opcional
  - `symbols` (STRING) - Opcional, array de símbolos
  - `type` (ENUM) - Opcional, FULL ou MINI
- **Fonte de dados:** Memory
- **Retorno:** Estatísticas de 24h incluindo priceChange, priceChangePercent, weightedAvgPrice, prevClosePrice, lastPrice, volume, quoteVolume, etc. [1]

**c) Tickers - Latest Price**
```
GET /api/v3/ticker/price
```
- **Peso:** 1-2 dependendo do número de símbolos
- **Parâmetros:**
  - `symbol` (STRING) - Opcional
  - `symbols` (STRING) - Opcional
- **Fonte de dados:** Memory
- **Retorno:** Preço atual para símbolo(s) [1]

**d) Order Book**
```
GET /api/v3/depth
```
- **Peso:** 1-50 baseado no limit
- **Parâmetros:**
  - `symbol` (STRING) - Obrigatório
  - `limit` (INT) - Opcional, padrão 100, máximo 5000
- **Fonte de dados:** Memory
- **Retorno:** `{lastUpdateId, bids: [[price, qty]], asks: [[price, qty]]}` [1]

**e) Recent Trades**
```
GET /api/v3/trades
```
- **Peso:** 1
- **Parâmetros:**
  - `symbol` (STRING) - Obrigatório
  - `limit` (INT) - Opcional, padrão 500, máximo 1000
- **Fonte de dados:** Memory
- **Retorno:** Array de trades recentes com id, price, qty, quoteQty, time, isBuyerMaker, isBestMatch [1]

**f) Aggregate Trades**
```
GET /api/v3/aggTrades
```
- **Peso:** 1
- **Parâmetros:**
  - `symbol` (STRING) - Obrigatório
  - `fromId` (LONG) - Opcional
  - `startTime` (LONG) - Opcional
  - `endTime` (LONG) - Opcional
  - `limit` (INT) - Opcional, padrão 500, máximo 1000
- **Fonte de dados:** Database
- **Retorno:** Trades agregados com quantidades somadas [1]

**g) Exchange Information**
```
GET /api/v3/exchangeInfo
```
- **Peso:** 10
- **Parâmetros:**
  - `symbol` (STRING) - Opcional
  - `symbols` (STRING) - Opcional
  - `permissions` (STRING) - Opcional
- **Fonte de dados:** Memory
- **Retorno:** Informações completas de trading incluindo rate limits, filtros, símbolos e permissões [1]

### 2.2 API Futures (USDⓈ-M)

**Base URL:** `https://fapi.binance.com`

**Endpoints principais:**
- `GET /fapi/v1/klines` - Klines com peso baseado no limit (1-10)
- `GET /fapi/v1/depth` - Order book
- `GET /fapi/v1/ticker/24hr` - Estatísticas 24h
- `GET /fapi/v1/exchangeInfo` - Informações da exchange [2]

---

## 3. Rate Limits

### 3.1 API Spot

A API Spot utiliza três tipos de rate limiters [1]:

**a) REQUEST_WEIGHT**
- Intervalo: 1 minuto
- Limite: 1200 por minuto
- Cada endpoint tem um peso diferente

**b) ORDERS**
- Intervalo: 1 segundo
- Limite: 10 ordens por segundo
- Intervalo: 1 dia
- Limite: 200,000 ordens por dia

**c) RAW_REQUESTS**
- Intervalo: 5 minutos
- Limite: 5000 por 5 minutos

**Pesos por endpoint (exemplos):**
- `/api/v3/ping`: 1
- `/api/v3/time`: 1
- `/api/v3/exchangeInfo`: 10
- `/api/v3/depth` (limit 1-100): 1, (101-500): 5, (501-1000): 10, (1001-5000): 50
- `/api/v3/klines`: 1
- `/api/v3/ticker/24hr`: 1 (1 símbolo) ou 40 (todos símbolos)
- `POST /api/v3/order`: 1
- `GET /api/v3/openOrders`: 3 (1 símbolo) ou 40 (todos)

### 3.2 API Futures

- **Request Weight:** 1200 por minuto
- **Order Rate:** 10 ordens por segundo, 100,000 ordens por dia
- **Pesos específicos por endpoint** [2]

### 3.3 Cabeçalhos de Controle

Cada resposta inclui headers com informações de uso:
- `X-MBX-USED-WEIGHT-(intervalNum)(intervalLetter)` - Peso usado
- `X-MBX-ORDER-COUNT-(intervalNum)(intervalLetter)` - Contagem de ordens
- `Retry-After` - Segundos para esperar após 429 ou 418 [1]

**Importante:** Limites são baseados no IP, não na API key. Violações repetidas resultam em banimento automático (HTTP 418) com duração de 2 minutos a 3 dias [1].

---

## 4. Métodos de Autenticação

### 4.1 Tipos de Segurança

A API possui diferentes níveis de segurança [1]:

- **NONE:** Acesso livre (endpoints públicos)
- **TRADE:** Requer API-Key e assinatura
- **USER_DATA:** Requer API-Key e assinatura
- **USER_STREAM:** Requer API-Key
- **MARKET_DATA:** Requer API-Key

### 4.2 Endpoints SIGNED

Endpoints `TRADE` e `USER_DATA` são `SIGNED` e requerem:

1. **API Key** enviada no header `X-MBX-APIKEY`
2. **Timestamp** (milissegundos) no parâmetro `timestamp`
3. **Signature** (HMAC SHA256) no parâmetro `signature`

### 4.3 Geração de Assinatura

```python
import hmac
import hashlib

# secretKey é a chave secreta da API
# totalParams é a query string + request body concatenados
signature = hmac.new(
    secretKey.encode('utf-8'),
    totalParams.encode('utf-8'),
    hashlib.sha256
).hexdigest()
```

### 4.4 Parâmetros de Segurança

- `timestamp`: Timestamp de quando a requisição foi criada
- `recvWindow` (opcional): Janela de validade em ms (padrão 5000, máximo 60000)
- Validação: `timestamp` deve estar dentro de `recvWindow` do tempo do servidor [1]

### 4.5 Exemplo de Requisição SIGNED

```bash
curl -H "X-MBX-APIKEY: <api_key>" \
-X POST 'https://api.binance.com/api/v3/order?symbol=BTCUSDT&side=BUY&type=LIMIT&timeInForce=GTC&quantity=1&price=50000&recvWindow=5000&timestamp=1499827319559&signature=<signature>'
```

---

## 5. Como Obter Todos os Pares USDT

### 5.1 Método 1: Usando exchangeInfo

```python
import requests

def get_usdt_pairs():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(url)
    data = response.json()
    
    usdt_pairs = []
    for symbol in data['symbols']:
        if symbol['quoteAsset'] == 'USDT' and symbol['status'] == 'TRADING':
            usdt_pairs.append(symbol['symbol'])
    
    return usdt_pairs

# Uso
pairs = get_usdt_pairs()
print(f"Total de pares USDT: {len(pairs)}")
```

### 5.2 Método 2: Usando ticker/price

```python
def get_usdt_pairs_from_ticker():
    url = "https://api.binance.com/api/v3/ticker/price"
    response = requests.get(url)
    data = response.json()
    
    usdt_pairs = [item['symbol'] for item in data if item['symbol'].endswith('USDT')]
    return usdt_pairs
```

### 5.3 Considerações

- A lista de pares muda frequentemente (novos listados, delistados)
- Sempre verificar o `status` do símbolo em `exchangeInfo`
- Alguns pares podem estar em `PRE_TRADING` ou `POST_TRADING` [1]

---

## 6. Exemplos de Implementação em Python

### 6.1 Usando requests (API Nativa)

#### Exemplo 1: Obter Klines de todos os pares USDT

```python
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

BASE_URL = "https://api.binance.com"

def get_usdt_pairs():
    """Obter lista de todos os pares USDT ativos"""
    response = requests.get(f"{BASE_URL}/api/v3/exchangeInfo")
    data = response.json()
    return [s['symbol'] for s in data['symbols'] 
            if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']

def get_klines(symbol, interval='1h', limit=1000):
    """Obter dados kline/candlestick para um símbolo"""
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    response = requests.get(f"{BASE_URL}/api/v3/klines", params=params)
    
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        df['symbol'] = symbol
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    else:
        print(f"Erro para {symbol}: {response.status_code}")
        return None

def fetch_all_klines(interval='1h', limit=1000, max_workers=10):
    """Obter klines para todos os pares USDT usando multithreading"""
    pairs = get_usdt_pairs()
    all_data = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_symbol = {
            executor.submit(get_klines, symbol, interval, limit): symbol 
            for symbol in pairs
        }
        
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                df = future.result()
                if df is not None:
                    all_data.append(df)
                print(f"✓ {symbol} concluído")
            except Exception as e:
                print(f"✗ {symbol} falhou: {e}")
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()

# Uso
if __name__ == "__main__":
    print("Obtendo lista de pares USDT...")
    pairs = get_usdt_pairs()
    print(f"Total: {len(pairs)} pares")
    
    print("\nColetando dados históricos...")
    df = fetch_all_klines(interval='1h', limit=500)
    
    if not df.empty:
        print(f"Dados coletados: {len(df)} registros")
        print(df.head())
        # Salvar em CSV
        df.to_csv('binance_usdt_klines.csv', index=False)
```

#### Exemplo 2: Obter Order Book

```python
def get_order_book(symbol, limit=100):
    """Obter order book para um símbolo"""
    params = {'symbol': symbol, 'limit': limit}
    response = requests.get(f"{BASE_URL}/api/v3/depth", params=params)
    
    if response.status_code == 200:
        data = response.json()
        bids = pd.DataFrame(data['bids'], columns=['price', 'quantity'])
        asks = pd.DataFrame(data['asks'], columns=['price', 'quantity'])
        return bids, asks
    else:
        print(f"Erro: {response.status_code}")
        return None, None

# Uso
bids, asks = get_order_book('BTCUSDT', limit=20)
print("Bids (ordens de compra):")
print(bids)
print("\nAsks (ordens de venda):")
print(asks)
```

#### Exemplo 3: Obter Tickers e Volume

```python
def get_24hr_tickers(symbols=None):
    """Obter estatísticas de 24h para um ou todos os símbolos"""
    url = f"{BASE_URL}/api/v3/ticker/24hr"
    
    if symbols:
        params = {'symbols': str(symbols).replace("'", '"')}
    else:
        params = {}
    
    response = requests.get(url, params=params)
    return response.json()

# Uso
# Para todos os símbolos
all_tickers = get_24hr_tickers()
print(f"Total de símbolos: {len(all_tickers)}")

# Para símbolos específicos
btc_ticker = get_24hr_tickers(['BTCUSDT', 'ETHUSDT'])
print(btc_ticker)
```

#### Exemplo 4: Rate Limiting Manual

```python
import time
from datetime import datetime, timedelta

class BinanceAPIClient:
    def __init__(self, base_url="https://api.binance.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.request_times = []
        self.weight_per_minute = 1200
        self.weight_used = 0
        self.last_reset = datetime.now()
    
    def _check_rate_limit(self):
        """Verificar e respeitar rate limits"""
        now = datetime.now()
        
        # Resetar contador a cada minuto
        if (now - self.last_reset).seconds >= 60:
            self.weight_used = 0
            self.last_reset = now
        
        # Se excedeu o limite, esperar
        if self.weight_used >= self.weight_per_minute:
            wait_time = 60 - (now - self.last_reset).seconds
            print(f"Rate limit atingido. Aguardando {wait_time} segundos...")
            time.sleep(wait_time + 1)
            self.weight_used = 0
            self.last_reset = datetime.now()
    
    def make_request(self, endpoint, params=None):
        """Fazer requisição com rate limiting"""
        self._check_rate_limit()
        
        response = self.session.get(
            f"{self.base_url}{endpoint}",
            params=params
        )
        
        # Extrair peso do header
        weight_header = response.headers.get('X-MBX-USED-WEIGHT-1M')
        if weight_header:
            self.weight_used = int(weight_header)
        
        return response.json()

# Uso
client = BinanceAPIClient()
klines = client.make_request('/api/v3/klines', {
    'symbol': 'BTCUSDT',
    'interval': '1h',
    'limit': 1000
})
```

### 6.2 Usando CCXT Library

A biblioteca CCXT oferece uma interface unificada para múltiplas exchanges [3][4].

#### Instalação

```bash
pip install ccxt
```

#### Exemplo 1: Conexão e Mercados

```python
import ccxt
import pandas as pd

# Inicializar exchange
binance = ccxt.binance({
    'apiKey': 'YOUR_API_KEY',      # Opcional para dados públicos
    'secret': 'YOUR_SECRET',       # Opcional para dados públicos
    'enableRateLimit': True,       # Habilitar rate limiting automático
})

# Carregar mercados (símbolos)
markets = binance.load_markets()
print(f"Total de símbolos: {len(markets)}")

# Filtrar pares USDT
usdt_pairs = [symbol for symbol in markets.keys() if symbol.endswith('/USDT')]
print(f"Pares USDT: {len(usdt_pairs)}")
```

#### Exemplo 2: Obter OHLCV (Klines)

```python
def fetch_ohlcv_data(symbol, timeframe='1h', limit=1000):
    """Obter dados OHLCV usando CCXT"""
    try:
        ohlcv = binance.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(
            ohlcv, 
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['symbol'] = symbol
        return df
    except Exception as e:
        print(f"Erro ao obter {symbol}: {e}")
        return None

# Uso
btc_data = fetch_ohlcv_data('BTC/USDT', '1d', 365)
print(btc_data.head())
```

#### Exemplo 3: Obter Tickers

```python
# Obter ticker de um símbolo
ticker = binance.fetch_ticker('BTC/USDT')
print(f"Preço atual: {ticker['last']}")
print(f"Volume 24h: {ticker['baseVolume']}")
print(f"Quote Volume: {ticker['quoteVolume']}")

# Obter tickers de todos os símbolos
all_tickers = binance.fetch_tickers()
print(f"Total de tickers: {len(all_tickers)}")

# Filtrar apenas USDT
usdt_tickers = {k: v for k, v in all_tickers.items() if k.endswith('/USDT')}
```

#### Exemplo 4: Obter Order Book

```python
def fetch_order_book(symbol, limit=20):
    """Obter order book"""
    try:
        order_book = binance.fetch_order_book(symbol, limit)
        return order_book
    except Exception as e:
        print(f"Erro: {e}")
        return None

# Uso
ob = fetch_order_book('BTC/USDT', 50)
if ob:
    bids = pd.DataFrame(ob['bids'], columns=['price', 'amount'])
    asks = pd.DataFrame(ob['asks'], columns=['price', 'amount'])
    print("Bids:")
    print(bids.head())
    print("\nAsks:")
    print(asks.head())
```

#### Exemplo 5: Coletar Dados de Múltiplos Pares

```python
def fetch_all_usdt_data(timeframe='1h', limit=1000):
    """Coletar dados OHLCV de todos os pares USDT"""
    # Carregar mercados
    binance.load_markets()
    
    # Filtrar pares USDT ativos
    usdt_pairs = [
        symbol for symbol, info in binance.markets.items() 
        if symbol.endswith('/USDT') and info['active']
    ]
    
    all_data = []
    
    for symbol in usdt_pairs[:10]:  # Limitar a 10 para exemplo
        try:
            df = fetch_ohlcv_data(symbol, timeframe, limit)
            if df is not None:
                all_data.append(df)
            print(f"✓ {symbol} coletado")
            time.sleep(0.1)  # Rate limiting adicional
        except Exception as e:
            print(f"✗ {symbol} falhou: {e}")
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()

# Uso
data = fetch_all_usdt_data('4h', 500)
```

#### Exemplo 6: Com Autenticação (Dados Privados)

```python
# Inicializar com credenciais
binance_auth = ccxt.binance({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET',
    'enableRateLimit': True,
})

# Obter saldo da conta
balance = binance_auth.fetch_balance()
print(balance['USDT'])

# Obter ordens abertas
open_orders = binance_auth.fetch_open_orders('BTC/USDT')
print(f"Ordens abertas: {len(open_orders)}")
```

### 6.3 Comparação: requests vs CCXT

| Característica | requests (nativo) | CCXT |
|----------------|-------------------|------|
| **Controle** | Total | Limitado |
| **Setup** | Simples | Simples |
| **Rate Limiting** | Manual | Automático |
| **Multi-exchange** | Não | Sim (100+ exchanges) |
| **Dados privados** | Sim | Sim |
| **Estrutura de dados** | Customizável | Padronizada |
| **Performance** | Ligeiramente superior | Boa |
| **Manutenção** | Responsabilidade do usuário | Mantida pela comunidade |

**Recomendação:** Use CCXT para prototipagem rápida e suporte multi-exchange. Use requests nativo para performance máxima e controle detalhado.

---

## 7. CCXT Library - Alternativa Abrangente

### 7.1 Vantagens do CCXT

1. **Unificação:** Mesma API para 100+ exchanges
2. **Rate Limiting Automático:** Implementa limites de cada exchange automaticamente
3. **Estrutura Padronizada:** Dados retornados no mesmo formato independente da exchange
4. **Suporte Completo:** Mercados, tickers, order books, OHLCV, trades, ordens, saldos
5. **Comunidade Ativa:** Mantida por desenvolvedores e comunidade
6. **Multi-linguagem:** Python, JavaScript, PHP [3][4]

### 7.2 Desvantagens

1. **Overhead:** Camada adicional de abstração
2. **Latência:** Ligeiramente maior que API nativa
3. **Customização:** Menos flexível para casos específicos
4. **Atualizações:** Pode haver delay em suporte a novos endpoints

### 7.3 Rate Limiting no CCXT

```python
import ccxt
import time

exchange = ccxt.binance({
    'enableRateLimit': True,  # Habilitar rate limiting automático
    'rateLimit': 1000,        # Override do rate limit (ms)
})

# O CCXT gerencia automaticamente:
# - Delay entre requisições
# - Retry em caso de 429
# - Backoff exponencial
```

### 7.4 Exemplo Completo CCXT

```python
import ccxt
import pandas as pd
from datetime import datetime

class BinanceDataCollector:
    def __init__(self, api_key=None, secret=None):
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
            'timeout': 30000,
        })
    
    def get_usdt_pairs(self):
        """Obter todos os pares USDT ativos"""
        self.exchange.load_markets()
        pairs = [
            symbol for symbol, info in self.exchange.markets.items()
            if symbol.endswith('/USDT') and info['active']
        ]
        return pairs
    
    def fetch_historical_data(self, symbol, timeframe='1h', days=30):
        """Obter dados históricos para um símbolo"""
        # Calcular limit baseado no timeframe e dias
        timeframe_minutes = self.exchange.parse_timeframe(timeframe)
        limit = int((days * 24 * 60) / timeframe_minutes)
        
        since = self.exchange.parse8601(
            (datetime.utcnow() - timedelta(days=days)).isoformat()
        )
        
        ohlcv = self.exchange.fetch_ohlcv(
            symbol, timeframe, since=since, limit=limit
        )
        
        df = pd.DataFrame(
            ohlcv,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['symbol'] = symbol
        return df
    
    def fetch_all_usdt_data(self, timeframe='1h', days=7, max_pairs=None):
        """Coletar dados de todos os pares USDT"""
        pairs = self.get_usdt_pairs()
        
        if max_pairs:
            pairs = pairs[:max_pairs]
        
        all_data = []
        
        for symbol in pairs:
            try:
                df = self.fetch_historical_data(symbol, timeframe, days)
                all_data.append(df)
                print(f"✓ {symbol}: {len(df)} registros")
            except Exception as e:
                print(f"✗ {symbol}: {e}")
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame()

# Uso
collector = BinanceDataCollector()
data = collector.fetch_all_usdt_data('1h', days=30, max_pairs=50)
```

---

## 8. Melhores Práticas

### 8.1 Rate Limiting

1. **Sempre habilitar rate limiting** (CCXT: `enableRateLimit=True`)
2. **Implementar retry com backoff** para erros 429/418
3. **Monitorar headers** `X-MBX-USED-WEIGHT-*`
4. **Distribuir requisições** ao longo do tempo
5. **Usar multithreading com cuidado** - limite por IP

### 8.2 Tratamento de Erros

```python
def safe_request(func, *args, max_retries=3, **kwargs):
    """Executar requisição com retry"""
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = (2 ** attempt) + 1  # Backoff exponencial
            time.sleep(wait_time)
```

### 8.3 Logging e Monitoramento

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def monitored_request(endpoint, params):
    logger.info(f"Requisição: {endpoint}, params: {params}")
    response = requests.get(endpoint, params=params)
    logger.info(f"Status: {response.status_code}, Weight: {response.headers.get('X-MBX-USED-WEIGHT-1M')}")
    return response.json()
```

### 8.4 Persistência de Dados

```python
def save_data(df, filename, format='parquet'):
    """Salvar dados em formato eficiente"""
    if format == 'parquet':
        df.to_parquet(filename, compression='snappy')
    elif format == 'csv':
        df.to_csv(filename, index=False)
    elif format == 'hdf5':
        df.to_hdf(filename, key='data', mode='w')
```

### 8.5 Considerações de Performance

1. **Multithreading:** Use `ThreadPoolExecutor` para coletar múltiplos símbolos
2. **Batch requests:** Quando possível, use endpoints que retornam múltiplos símbolos
3. **Cache:** Armazene `exchangeInfo` localmente (muda raramente)
4. **Incremental updates:** Para dados históricos, busque apenas novos dados
5. **Compression:** Use gzip para reduzir tráfego

---

## 9. Diferenças entre Binance.com e Binance US

**Binance US** (`api.binance.us`) tem:
- Base URL diferente
- Alguns endpoints podem variar
- Regulamentação diferente (EUA)
- Mesma estrutura geral de API [1]

Para uso geral, a API global (`api.binance.com`) é recomendada.

---

## 10. Futuros (Futures API)

### 10.1 USDⓈ-M Futures

**Base URL:** `https://fapi.binance.com`

**Endpoints principais:**
- `GET /fapi/v1/klines` - Klines
- `GET /fapi/v1/depth` - Order book
- `GET /fapi/v1/ticker/24hr` - Ticker 24h
- `GET /fapi/v1/exchangeInfo` - Informações
- `GET /fapi/v1/continuousKlines` - Klines de contratos perpétuos
- `GET /fapi/v1/indexPriceKlines` - Klines de preço índice
- `GET /fapi/v1/markPriceKlines` - Klines de mark price
- `GET /fapi/v1/fundingRate` - Taxa de funding

**Rate Limits:**
- 1200 weight por minuto
- 10 ordens por segundo
- 100,000 ordens por dia [2]

### 10.2 COIN-M Futures

**Base URL:** `https://dapi.binance.com`

Endpoints similares a USDⓈ-M, mas para contratos denominados em cripto.

---

## 11. Exemplo Completo: Coletor de Dados USDT

```python
"""
Coletor completo de dados da Binance para pares USDT
Suporta: Spot e Futures
"""
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BinanceUSDTCollector:
    def __init__(self, base_url="https://api.binance.com", 
                 api_key=None, api_secret=None):
        self.base_url = base_url
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'X-MBX-APIKEY': api_key})
        self.api_key = api_key
        self.api_secret = api_secret
        
        # Rate limiting
        self.max_weight_per_minute = 1200
        self.current_weight = 0
        self.weight_reset_time = time.time()
    
    def _rate_limit_check(self):
        """Verificar rate limit"""
        now = time.time()
        if now - self.weight_reset_time >= 60:
            self.current_weight = 0
            self.weight_reset_time = now
        
        if self.current_weight >= self.max_weight_per_minute:
            sleep_time = 60 - (now - self.weight_reset_time)
            logger.warning(f"Rate limit atingido. Aguardando {sleep_time:.1f}s")
            time.sleep(sleep_time + 1)
            self.current_weight = 0
            self.weight_reset_time = time.time()
    
    def _request(self, endpoint: str, params: Dict = None, 
                 signed: bool = False) -> Dict:
        """Fazer requisição com rate limiting"""
        self._rate_limit_check()
        
        url = f"{self.base_url}{endpoint}"
        
        if signed and self.api_key and self.api_secret:
            params = params or {}
            params['timestamp'] = int(time.time() * 1000)
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            params['signature'] = signature
        
        response = self.session.get(url, params=params)
        
        # Atualizar contador de peso
        weight = response.headers.get('X-MBX-USED-WEIGHT-1M')
        if weight:
            self.current_weight = int(weight)
        
        if response.status_code != 200:
            logger.error(f"Erro {response.status_code}: {response.text}")
            response.raise_for_status()
        
        return response.json()
    
    def get_exchange_info(self) -> Dict:
        """Obter informações da exchange"""
        return self._request('/api/v3/exchangeInfo')
    
    def get_usdt_pairs(self) -> List[str]:
        """Obter lista de pares USDT ativos"""
        info = self.get_exchange_info()
        pairs = []
        for symbol in info['symbols']:
            if (symbol['quoteAsset'] == 'USDT' and 
                symbol['status'] == 'TRADING' and
                symbol['isSpotTradingAllowed']):
                pairs.append(symbol['symbol'])
        return pairs
    
    def get_klines(self, symbol: str, interval: str = '1h', 
                   start_time: Optional[int] = None,
                   end_time: Optional[int] = None,
                   limit: int = 1000) -> pd.DataFrame:
        """Obter klines para um símbolo"""
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        data = self._request('/api/v3/klines', params)
        
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        # Converter tipos
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 
                       'quote_volume', 'taker_buy_base', 'taker_buy_quote']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['symbol'] = symbol
        return df
    
    def get_24hr_tickers(self, symbols: List[str] = None) -> pd.DataFrame:
        """Obter tickers de 24h"""
        params = {}
        if symbols:
            params['symbols'] = str(symbols).replace("'", '"')
        
        data = self._request('/api/v3/ticker/24hr', params)
        return pd.DataFrame(data)
    
    def get_order_book(self, symbol: str, limit: int = 100) -> Dict:
        """Obter order book"""
        params = {'symbol': symbol, 'limit': limit}
        return self._request('/api/v3/depth', params)
    
    def fetch_all_usdt_klines(self, interval: str = '1h', 
                             limit: int = 1000,
                             max_workers: int = 10) -> pd.DataFrame:
        """Coletar klines de todos os pares USDT"""
        pairs = self.get_usdt_pairs()
        logger.info(f"Coletando dados de {len(pairs)} pares USDT")
        
        all_data = []
        
        # Usar ThreadPoolExecutor para paralelismo
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.get_klines, symbol, interval, None, None, limit): symbol
                for symbol in pairs
            }
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    df = future.result()
                    if not df.empty:
                        all_data.append(df)
                    logger.info(f"✓ {symbol} concluído")
                except Exception as e:
                    logger.error(f"✗ {symbol} falhou: {e}")
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame()

# Uso principal
if __name__ == "__main__":
    import hmac
    import hashlib
    
    # Inicializar coletor (sem autenticação para dados públicos)
    collector = BinanceUSDTCollector()
    
    # 1. Obter pares USDT
    pairs = collector.get_usdt_pairs()
    print(f"Pares USDT encontrados: {len(pairs)}")
    print(f"Exemplos: {pairs[:5]}")
    
    # 2. Coletar dados históricos (limitado a 5 pares para exemplo)
    sample_pairs = pairs[:5]
    for pair in sample_pairs:
        try:
            df = collector.get_klines(pair, interval='1h', limit=100)
            print(f"\n{pair}: {len(df)} klines")
            print(df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].head())
        except Exception as e:
            print(f"Erro com {pair}: {e}")
    
    # 3. Obter tickers 24h
    tickers = collector.get_24hr_tickers(sample_pairs)
    print("\nTickers 24h:")
    print(tickers[['symbol', 'lastPrice', 'volume', 'quoteVolume']].to_string())
    
    # 4. Obter order book
    if sample_pairs:
        ob = collector.get_order_book(sample_pairs[0], limit=5)
        print(f"\nOrder Book de {sample_pairs[0]}:")
        print("Bids:", ob['bids'][:3])
        print("Asks:", ob['asks'][:3])
```

---

## 12. Referências e Fontes

[1] Binance US API Documentation - REST API. GitHub. Disponível em: https://github.com/binance-us/binance-us-api-docs/blob/master/rest-api.md

[2] Binance Futures API Documentation - Kline Candlestick Data. Binance Developers. Disponível em: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data

[3] CCXT Library Documentation. GitHub. Disponível em: https://github.com/ccxt/ccxt

[4] Adnan Siddiqi. CCXT Python Tutorial: Fetch OHLCV, Ticker & Order Book Data. Blog. Disponível em: https://blog.adnansiddiqi.me/getting-started-with-ccxt-crypto-exchange-library-and-python/

[5] imwatsi. Use Python to Retrieve All USDT Trading Pairs on Binance. Steemit. Disponível em: https://steemit.com/utopianio/@imwatsi/use-python-to-retrieve-all-usdt-trading-pairs-on-binance-and-filter-by-price-vs-ema

---

## 13. Conclusão

A API da Binance oferece endpoints robustos para coleta de dados de mercado. Para projetos simples, a API nativa com `requests` oferece máximo controle e performance. Para projetos multi-exchange ou prototipagem rápida, o CCXT é excelente escolha.

**Pontos críticos:**
1. Sempre respeitar rate limits para evitar banimento
2. Implementar retry com backoff exponencial
3. Usar multithreading com moderação
4. Monitorar headers de controle
5. Armazenar dados em formatos eficientes (Parquet, HDF5)

A coleta de todos os pares USDT é viável com multithreading, mas exige cuidado com rate limits. A lista de pares deve ser obtida do `exchangeInfo` e filtrada por `quoteAsset == 'USDT'` e `status == 'TRADING'`.

Para dados históricos extensivos, considere usar a API de Futures que permite até 1500 klines por requisição, ou implemente paginação manual coletando dados em lotes.

---

**Fim do Relatório**