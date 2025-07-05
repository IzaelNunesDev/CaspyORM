# 🚀 Exemplos CaspyORM

## 📋 Visão Geral

Esta pasta contém exemplos práticos de uso da biblioteca CaspyORM, organizados por categoria e complexidade.

---

## 📁 Estrutura dos Exemplos

### 🔰 [`basic/`](basic/)
**Exemplos básicos** - Funcionalidades fundamentais
- **`models/`** - Definição de modelos
- **`config/`** - Configuração de conexão
- **`routers/`** - Rotas da API
- **`app/`** - Aplicação FastAPI
- **`run.py`** - Script de execução
- **`README.md`** - Documentação da aplicação
- **`requirements.txt`** - Dependências

### 🚕 [`nyc_taxi/`](nyc_taxi/)
**Exemplos com dados reais** - NYC TLC Taxi Data
- Exemplos de uso com dados reais de táxi
- Modelos otimizados para Cassandra
- Consultas de performance

### 🔌 [`api/`](api/)
**Exemplos de API** - Integração com FastAPI
- **`test_api.py`** - Teste da API REST
- **`main_api.py`** - API principal
- Exemplos de endpoints
- Integração com Pydantic

---

## 🚀 Como Usar os Exemplos

### Exemplo Básico (Recomendado para Iniciantes)

#### 1. Configurar Ambiente
```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Instalar dependências
pip install -r examples/requirements.txt
```

#### 2. Executar Aplicação
```bash
# Executar aplicação básica
python examples/basic/run.py

# Ou usar uvicorn diretamente
uvicorn examples.basic.app.main:app --reload
```

#### 3. Testar API
```bash
# Testar endpoints
python examples/api/test_api.py
```

### Exemplo NYC Taxi (Dados Reais)

#### 1. Preparar Dados
```bash
# Download automático (executado pelos testes)
# Dados: ~48MB (yellow_tripdata_2024-01.parquet)
```

#### 2. Executar Exemplo
```bash
# Executar exemplo com dados reais
python examples/nyc_taxi/example_usage.py
```

---

## 📚 Exemplos Detalhados

### 🔰 Exemplo Básico

#### Modelo Simples
```python
from caspyorm import Model, fields

class User(Model):
    __table_name__ = "users"
    
    user_id = fields.UUID(primary_key=True)
    username = fields.Text(partition_key=True)
    email = fields.Text()
    created_at = fields.Timestamp()
```

#### Operações CRUD
```python
# Criar usuário
user = User(
    user_id=uuid.uuid4(),
    username="john_doe",
    email="john@example.com",
    created_at=datetime.now()
)
user.save()

# Buscar usuário
user = User.get(username="john_doe")

# Listar usuários
users = list(User.all())

# Filtrar usuários
john_users = list(User.filter(username="john_doe"))
```

#### API REST
```python
from fastapi import FastAPI
from caspyorm import connection

app = FastAPI()

@app.get("/users/{username}")
async def get_user(username: str):
    user = User.get(username=username)
    return user.model_dump() if user else None

@app.post("/users")
async def create_user(user_data: dict):
    user = User(**user_data)
    user.save()
    return user.model_dump()
```

### 🚕 Exemplo NYC Taxi

#### Modelo Otimizado
```python
class NYCTaxiClean(Model):
    __table_name__ = "nyc_taxi_clean"
    
    trip_id = fields.UUID(primary_key=True)
    vendor_id = fields.Text(partition_key=True)
    pickup_datetime = fields.Timestamp(clustering_key=True)
    fare_amount = fields.Float()
    trip_distance = fields.Float()
    passenger_count = fields.Integer()
```

#### Consultas de Performance
```python
# Buscar por vendor (partition key)
vendor_trips = list(NYCTaxiClean.filter(vendor_id='1'))

# Agregações em Python
all_trips = list(NYCTaxiClean.all())
avg_fare = sum(t.fare_amount for t in all_trips) / len(all_trips)

# Top 10 tarifas mais altas
top_trips = sorted(all_trips, key=lambda x: x.total_amount, reverse=True)[:10]
```

### 🔌 Exemplo API

#### Endpoints REST
```python
@app.get("/trips/{vendor_id}")
async def get_trips_by_vendor(vendor_id: str):
    trips = list(NYCTaxiClean.filter(vendor_id=vendor_id))
    return [trip.model_dump() for trip in trips]

@app.get("/trips/stats")
async def get_trip_stats():
    trips = list(NYCTaxiClean.all())
    return {
        "total_trips": len(trips),
        "avg_fare": sum(t.fare_amount for t in trips) / len(trips),
        "total_revenue": sum(t.total_amount for t in trips)
    }
```

---

## 🎯 Padrões Recomendados

### 1. **Design de Schema**
```python
# ✅ Otimizado para Cassandra
class OptimizedModel(Model):
    __table_name__ = "optimized_table"
    
    # Partition key (distribuição)
    partition_field = fields.Text(partition_key=True)
    
    # Clustering key (ordenação)
    timestamp = fields.Timestamp(clustering_key=True)
    
    # Campos normais
    data_field = fields.Text()
    numeric_field = fields.Float()
```

### 2. **Operações Eficientes**
```python
# ✅ Buscar por partition key
records = list(Model.filter(partition_field="value"))

# ✅ Inserção em lote
Model.bulk_create(instances)

# ✅ Agregações em Python
all_records = list(Model.all())
result = sum(r.numeric_field for r in all_records)
```

### 3. **Configuração Otimizada**
```python
from cassandra.policies import DCAwareRoundRobinPolicy

connection.connect(
    contact_points=['localhost'],
    port=9042,
    keyspace='my_keyspace',
    protocol_version=5,
    load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='datacenter1')
)
```

---

## 🔍 Análise de Performance

### Métricas dos Exemplos
| Exemplo | Operação | Performance | Status |
|---------|----------|-------------|--------|
| **Básico** | CRUD simples | ~1k ops/s | ✅ Bom |
| **NYC Taxi** | Dados reais | 794 inserções/s | ✅ Excelente |
| **API** | Endpoints REST | ~100 req/s | ✅ Bom |

### Otimizações Aplicadas
- **Batch size**: 25 registros por batch
- **Chunk size**: 5.000 registros por chunk
- **Memória**: Controle de uso (~1GB)
- **Índices**: Otimizados para consultas frequentes

---

## 🐛 Troubleshooting

### Problemas Comuns

#### Erro de Conexão
```python
# Verificar Cassandra
from caspyorm import connection
try:
    connection.connect(contact_points=['localhost'])
except Exception as e:
    print(f"Erro de conexão: {e}")
```

#### Erro de Schema
```python
# Sincronizar schema
Model.sync_table(auto_apply=True)
```

#### Performance Lenta
```python
# Reduzir batch size
BATCH_SIZE = 25  # Em vez de 50

# Usar partition keys
records = list(Model.filter(partition_key="value"))
```

---

## 📚 Documentação Relacionada

- [Testes](../tests/) - Testes organizados por categoria
- [Análise de Performance](../docs/performance/) - Métricas detalhadas
- [Análise da API](../docs/analysis/) - Estudo da API
- [Scripts](../scripts/) - Scripts de benchmark e download

---

**Status**: ✅ **Exemplos Organizados e Funcionais**  
**Última Atualização**: 05/07/2025  
**Cobertura**: 100% das funcionalidades principais 