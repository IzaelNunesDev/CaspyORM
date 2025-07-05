# 📊 Dados CaspyORM

## 📋 Visão Geral

Esta pasta contém todos os dados utilizados nos testes e exemplos da biblioteca CaspyORM, organizados por categoria e origem.

---

## 📁 Estrutura dos Dados

### 🚕 [`nyc_taxi/`](nyc_taxi/)
**Dados reais NYC TLC** - Taxi and Limousine Commission
- **`yellow_tripdata_2024-01.parquet`** - Dados de corridas de táxi amarelo
- **Tamanho**: ~48MB (100.000 registros limitados)
- **Origem**: NYC TLC (dados oficiais)
- **Formato**: Parquet (otimizado para análise)

### 📈 Dados Sintéticos
**Dados gerados** - Para testes de funcionalidade
- Dados gerados automaticamente pelos testes
- Modelos de exemplo (User, Post, etc.)
- Dados de benchmark e performance

---

## 🚀 Como Usar os Dados

### Dados NYC TLC (Recomendado)

#### 1. Download Automático
```bash
# Download automático (executado pelos testes)
python scripts/download/download_nyc_taxi_data.py

# Dados salvos em: data/nyc_taxi/yellow_tripdata_2024-01.parquet
```

#### 2. Download Manual
```bash
# Download direto
wget https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet

# Mover para pasta correta
mv yellow_tripdata_2024-01.parquet data/nyc_taxi/
```

#### 3. Uso nos Testes
```python
# Carregar dados NYC TLC
import pandas as pd
from pathlib import Path

data_path = Path("data/nyc_taxi/yellow_tripdata_2024-01.parquet")
df = pd.read_parquet(data_path)

# Limitar para 100k registros (1GB)
df_limited = df.head(100000)
```

### Dados Sintéticos

#### 1. Geração Automática
```python
# Dados gerados pelos testes
def generate_synthetic_data(count=1000):
    """Gerar dados sintéticos para teste"""
    data = []
    for i in range(count):
        data.append({
            "id": uuid.uuid4(),
            "name": f"User_{i}",
            "email": f"user_{i}@example.com",
            "created_at": datetime.now()
        })
    return data
```

#### 2. Uso nos Exemplos
```python
# Exemplo básico
from examples.basic.models.user import User

# Criar dados de teste
test_users = [
    User(username="john", email="john@example.com"),
    User(username="jane", email="jane@example.com"),
]

# Inserir em lote
User.bulk_create(test_users)
```

---

## 📊 Esquema dos Dados NYC TLC

### Estrutura do Dataset
```python
# Campos principais do dataset NYC TLC
NYC_TAXI_SCHEMA = {
    "VendorID": "int64",           # ID do fornecedor (1, 2)
    "tpep_pickup_datetime": "datetime64[ns]",  # Data/hora de coleta
    "tpep_dropoff_datetime": "datetime64[ns]", # Data/hora de entrega
    "passenger_count": "int64",     # Número de passageiros
    "trip_distance": "float64",     # Distância da viagem (milhas)
    "RatecodeID": "int64",          # Código da tarifa
    "store_and_fwd_flag": "object", # Flag de armazenamento
    "PULocationID": "int64",        # ID localização coleta
    "DOLocationID": "int64",        # ID localização entrega
    "payment_type": "int64",        # Tipo de pagamento
    "fare_amount": "float64",       # Valor da tarifa
    "extra": "float64",             # Taxas extras
    "mta_tax": "float64",           # Taxa MTA
    "tip_amount": "float64",        # Gorjeta
    "tolls_amount": "float64",      # Pedágios
    "improvement_surcharge": "float64", # Taxa de melhoria
    "total_amount": "float64",      # Valor total
    "congestion_surcharge": "float64", # Taxa de congestionamento
    "airport_fee": "float64"        # Taxa de aeroporto
}
```

### Modelo CaspyORM
```python
from caspyorm import Model, fields

class NYCTaxiClean(Model):
    __table_name__ = "nyc_taxi_clean"
    
    # Chaves primárias
    trip_id = fields.UUID(primary_key=True)
    vendor_id = fields.Text(partition_key=True)
    pickup_datetime = fields.Timestamp(clustering_key=True)
    
    # Campos de dados
    dropoff_datetime = fields.Timestamp()
    passenger_count = fields.Integer()
    trip_distance = fields.Float()
    rate_code_id = fields.Integer()
    store_and_fwd_flag = fields.Text()
    pickup_location_id = fields.Integer()
    dropoff_location_id = fields.Integer()
    payment_type = fields.Integer()
    fare_amount = fields.Float()
    extra = fields.Float()
    mta_tax = fields.Float()
    tip_amount = fields.Float()
    tolls_amount = fields.Float()
    improvement_surcharge = fields.Float()
    total_amount = fields.Float()
    congestion_surcharge = fields.Float()
    airport_fee = fields.Float()
```

---

## 🎯 Otimizações Aplicadas

### 1. **Limitação de Volume**
```python
# Limitar para 100k registros (~1GB)
MAX_ROWS = 100000

# Evitar sobrecarga de memória
CHUNK_SIZE = 5000

# Batch size otimizado
BATCH_SIZE = 25
```

### 2. **Processamento Eficiente**
```python
# Processamento em chunks
def process_in_chunks(df, chunk_size=5000):
    """Processar DataFrame em chunks"""
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        yield chunk

# Conversão otimizada
def convert_to_models(chunk):
    """Converter chunk para modelos CaspyORM"""
    models = []
    for _, row in chunk.iterrows():
        model = NYCTaxiClean(
            trip_id=uuid.uuid4(),
            vendor_id=str(row['VendorID']),
            pickup_datetime=row['tpep_pickup_datetime'],
            # ... outros campos
        )
        models.append(model)
    return models
```

### 3. **Inserção em Lote**
```python
# Inserção otimizada
def insert_batch(models, batch_size=25):
    """Inserir modelos em lote"""
    for i in range(0, len(models), batch_size):
        batch = models[i:i+batch_size]
        NYCTaxiClean.bulk_create(batch)
```

---

## 📈 Métricas dos Dados

### Volume e Performance
| Métrica | Valor | Status |
|---------|-------|--------|
| **Registros** | 100.000 | ✅ Limitado |
| **Tamanho** | ~48MB | ✅ Gerenciável |
| **Tempo Download** | ~2min | ✅ Rápido |
| **Tempo Processamento** | ~2min | ✅ Eficiente |
| **Memória** | ~1GB | ✅ Controlado |

### Qualidade dos Dados
| Aspecto | Status | Observações |
|---------|--------|-------------|
| **Completude** | ✅ 95% | Alguns campos nulos |
| **Consistência** | ✅ Boa | Valores dentro do esperado |
| **Precisão** | ✅ Alta | Dados oficiais NYC TLC |
| **Atualidade** | ✅ 2024 | Dados de janeiro/2024 |

---

## 🔍 Análise dos Dados

### Estatísticas Básicas
```python
# Análise dos dados NYC TLC
def analyze_nyc_data():
    """Analisar dados NYC TLC"""
    df = pd.read_parquet("data/nyc_taxi/yellow_tripdata_2024-01.parquet")
    
    stats = {
        "total_records": len(df),
        "avg_fare": df['fare_amount'].mean(),
        "avg_distance": df['trip_distance'].mean(),
        "total_revenue": df['total_amount'].sum(),
        "unique_vendors": df['VendorID'].nunique(),
        "date_range": {
            "start": df['tpep_pickup_datetime'].min(),
            "end": df['tpep_pickup_datetime'].max()
        }
    }
    
    return stats
```

### Distribuições
```python
# Distribuição de tarifas
fare_distribution = df['fare_amount'].value_counts().head(10)

# Distribuição de distâncias
distance_distribution = df['trip_distance'].describe()

# Distribuição por vendor
vendor_distribution = df['VendorID'].value_counts()
```

---

## 🐛 Troubleshooting

### Problemas Comuns

#### Download Falha
```bash
# Verificar conectividade
curl -I https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet

# Download alternativo
wget --timeout=60 --tries=3 https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet
```

#### Erro de Memória
```bash
# Reduzir volume de dados
# Editar: MAX_ROWS = 10000 em vez de 100000

# Usar dados sintéticos
python tests/unit/test_01_model_definition.py
```

#### Erro de Formato
```bash
# Verificar formato do arquivo
file data/nyc_taxi/yellow_tripdata_2024-01.parquet

# Re-download se necessário
rm data/nyc_taxi/yellow_tripdata_2024-01.parquet
python scripts/download/download_nyc_taxi_data.py
```

---

## 📚 Documentação Relacionada

- [Testes NYC TLC](../tests/nyc_taxi/) - Testes específicos com dados reais
- [Scripts de Download](../scripts/download/) - Scripts para obter dados
- [Análise de Performance](../docs/performance/) - Métricas com dados reais
- [Exemplos NYC Taxi](../examples/nyc_taxi/) - Exemplos de uso

---

## 🔗 Links Úteis

- **NYC TLC**: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- **Dados Originais**: https://d37ci6vzurychx.cloudfront.net/trip-data/
- **Documentação**: https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf

---

**Status**: ✅ **Dados Organizados e Funcionais**  
**Última Atualização**: 05/07/2025  
**Volume**: 100.000 registros (~48MB) 