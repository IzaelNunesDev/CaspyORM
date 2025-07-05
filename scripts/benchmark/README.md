# Scripts de Benchmark

Este diretório contém scripts para executar benchmarks automatizados da CaspyORM e detectar regressões de performance.

## 📊 Scripts Disponíveis

### 1. `full_benchmark.py`
Script principal que executa todos os benchmarks de performance.

**Funcionalidades:**
- Inserção única (síncrona e assíncrona)
- Inserção em lote (síncrona e assíncrona)
- Consultas (síncrona e assíncrona)
- Atualizações (síncrona e assíncrona)
- Geração de métricas em JSON

**Uso:**
```bash
python scripts/benchmark/full_benchmark.py [opções]
```

**Opções:**
- `--contact-points`: Pontos de contato do Cassandra (padrão: localhost)
- `--keyspace`: Keyspace para testes (padrão: benchmark_keyspace)
- `--output`: Arquivo de saída JSON (padrão: benchmark_results.json)
- `--sync-only`: Executar apenas benchmarks síncronos
- `--async-only`: Executar apenas benchmarks assíncronos

### 2. `compare_results.py`
Script para comparar resultados de benchmark e detectar regressões.

**Funcionalidades:**
- Comparação de métricas entre baseline e resultados atuais
- Detecção automática de regressões
- Relatório detalhado de mudanças
- Saída em JSON para integração com CI/CD

**Uso:**
```bash
python scripts/benchmark/compare_results.py baseline.json current.json [opções]
```

**Opções:**
- `--output`: Arquivo de saída para comparação
- `--threshold`: Threshold para detectar mudanças (padrão: 0.1 = 10%)
- `--quiet`: Modo silencioso

### 3. `run_benchmarks.py`
Script automatizado que combina execução e comparação.

**Funcionalidades:**
- Execução automática de benchmarks
- Criação de baseline se não existir
- Comparação automática com baseline
- Integração com CI/CD

**Uso:**
```bash
python scripts/benchmark/run_benchmarks.py [opções]
```

**Opções:**
- `--contact-points`: Pontos de contato do Cassandra
- `--keyspace`: Keyspace para testes
- `--baseline`: Arquivo de baseline
- `--output`: Arquivo de saída para resultados atuais
- `--threshold`: Threshold para detectar regressões
- `--create-baseline`: Criar novo baseline
- `--skip-comparison`: Pular comparação com baseline

## 🚀 Uso Rápido

### Executar benchmark simples:
```bash
python scripts/benchmark/full_benchmark.py
```

### Criar baseline:
```bash
python scripts/benchmark/run_benchmarks.py --create-baseline
```

### Executar e comparar com baseline:
```bash
python scripts/benchmark/run_benchmarks.py
```

### Executar apenas benchmarks assíncronos:
```bash
python scripts/benchmark/full_benchmark.py --async-only
```

## 📈 Métricas Coletadas

### Latência
- `single_insert_latency`: Latência de inserção única
- `single_insert_async_latency`: Latência de inserção única assíncrona
- `bulk_insert_*_latency`: Latência de inserção em lote
- `query_latency`: Latência de consultas
- `query_async_latency`: Latência de consultas assíncronas
- `update_latency`: Latência de atualizações
- `update_async_latency`: Latência de atualizações assíncronas

### Throughput
- `single_insert_throughput`: Operações por segundo (inserção única)
- `single_insert_async_throughput`: Operações por segundo (inserção única assíncrona)
- `bulk_insert_*_throughput`: Operações por segundo (inserção em lote)
- `query_throughput`: Operações por segundo (consultas)
- `query_async_throughput`: Operações por segundo (consultas assíncronas)
- `update_throughput`: Operações por segundo (atualizações)
- `update_async_throughput`: Operações por segundo (atualizações assíncronas)

## 📊 Formato dos Resultados

Os resultados são salvos em JSON com a seguinte estrutura:

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "version": "0.1.0",
  "metrics": {
    "single_insert_latency": {
      "count": 1000,
      "min": 1.23,
      "max": 5.67,
      "mean": 2.45,
      "median": 2.34,
      "std": 0.89,
      "unit": "ms",
      "values": [1.23, 2.34, ...],
      "timestamp": "2024-01-01T12:00:00"
    },
    "single_insert_throughput": {
      "value": 408.16,
      "unit": "ops/s",
      "timestamp": "2024-01-01T12:00:00"
    }
  }
}
```

## 🔧 Integração com CI/CD

### GitHub Actions
```yaml
name: Performance Tests
on: [push, pull_request]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e .
          pip install cassandra-driver
      
      - name: Start Cassandra
        run: |
          # Iniciar Cassandra (exemplo)
          docker run -d --name cassandra -p 9042:9042 cassandra:latest
          sleep 30  # Aguardar inicialização
      
      - name: Run benchmarks
        run: |
          python scripts/benchmark/run_benchmarks.py \
            --contact-points localhost \
            --keyspace benchmark_keyspace \
            --baseline benchmark_baseline.json \
            --output benchmark_current.json \
            --threshold 0.15
```

### GitLab CI
```yaml
performance_test:
  stage: test
  script:
    - pip install -e .
    - pip install cassandra-driver
    - python scripts/benchmark/run_benchmarks.py
  artifacts:
    reports:
      junit: benchmark_results.xml
    paths:
      - benchmark_*.json
```

## 📋 Configuração do Ambiente

### Pré-requisitos
- Python 3.8+
- Cassandra rodando e acessível
- Dependências instaladas: `pip install -e .`

### Configuração do Cassandra
```bash
# Criar keyspace para benchmarks
cqlsh -e "CREATE KEYSPACE IF NOT EXISTS benchmark_keyspace 
          WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};"
```

## 🎯 Detecção de Regressões

O sistema detecta regressões quando:
- A latência aumenta mais que o threshold (padrão: 10%)
- O throughput diminui mais que o threshold (padrão: 10%)

### Exemplo de Regressão Detectada:
```
❌ REGRESSÕES DETECTADAS:
--------------------------------------------------
  single_insert_latency:
    2.45 → 3.12 ms
    Mudança: +27.3%

⚠️  1 regressões detectadas!
```

## 🔍 Análise de Resultados

### Comparação Manual
```bash
python scripts/benchmark/compare_results.py \
  baseline_v1.0.json \
  current_results.json \
  --threshold 0.1
```

### Análise de Tendências
```python
import json
import matplotlib.pyplot as plt

# Carregar resultados
with open('benchmark_results.json') as f:
    results = json.load(f)

# Plotar latência ao longo do tempo
latencies = results['metrics']['single_insert_latency']['values']
plt.plot(latencies)
plt.title('Latência de Inserção Única')
plt.ylabel('Latência (ms)')
plt.show()
```

## 🚨 Troubleshooting

### Erro de Conexão
```
❌ Erro ao conectar ao Cassandra
```
**Solução:** Verificar se o Cassandra está rodando e acessível.

### Erro de Keyspace
```
❌ Keyspace não existe
```
**Solução:** Criar o keyspace manualmente ou usar `--keyspace` diferente.

### Erro de Permissão
```
❌ Permissão negada para criar tabela
```
**Solução:** Verificar permissões do usuário no Cassandra.

### Benchmark Muito Lento
**Possíveis causas:**
- Cassandra sobrecarregado
- Rede lenta
- Hardware insuficiente

**Soluções:**
- Reduzir número de iterações
- Usar Cassandra local
- Verificar recursos do sistema 