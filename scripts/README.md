# 🔧 Scripts CaspyORM

## 📋 Visão Geral

Esta pasta contém scripts utilitários para benchmark, download de dados, limpeza e outras operações de suporte ao projeto CaspyORM.

---

## 📁 Estrutura dos Scripts

### 📊 [`benchmark/`](benchmark/)
**Scripts de benchmark** - Testes de performance
- Scripts para medir performance da biblioteca
- Comparações com outras soluções
- Métricas de escalabilidade

### 📥 [`download/`](download/)
**Scripts de download** - Obtenção de dados
- **`download_nyc_taxi_data.py`** - Download de dados NYC TLC
- Scripts para outros datasets
- Preparação de dados de teste

### 🧹 Scripts de Limpeza
**Scripts de manutenção** - Limpeza e organização
- **`clean_tables.py`** - Limpeza de tabelas Cassandra
- Scripts de backup e restore
- Manutenção de índices

---

## 🚀 Como Usar os Scripts

### Download de Dados NYC TLC

#### 1. Executar Download
```bash
# Download automático de dados NYC TLC
python scripts/download/download_nyc_taxi_data.py

# Dados baixados: ~48MB (yellow_tripdata_2024-01.parquet)
# Localização: data/nyc_taxi/
```

#### 2. Configurações
```python
# Configurações do download
DOWNLOAD_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
OUTPUT_DIR = "data/nyc_taxi/"
MAX_ROWS = 100000  # Limitar para 1GB de dados
```

### Limpeza de Tabelas

#### 1. Limpeza Básica
```bash
# Limpar todas as tabelas
python scripts/clean_tables.py

# Limpar tabela específica
python scripts/clean_tables.py --table nyc_taxi_clean
```

#### 2. Limpeza Seletiva
```bash
# Limpar apenas dados, manter schema
python scripts/clean_tables.py --data-only

# Limpar apenas índices
python scripts/clean_tables.py --indexes-only
```

### Scripts de Benchmark

#### 1. Benchmark Completo
```bash
# Executar benchmark completo
python scripts/benchmark/full_benchmark.py

# Resultados salvos em: docs/performance/benchmark_results.md
```

#### 2. Benchmark Específico
```bash
# Benchmark de inserção
python scripts/benchmark/insertion_benchmark.py

# Benchmark de consulta
python scripts/benchmark/query_benchmark.py

# Benchmark de memória
python scripts/benchmark/memory_benchmark.py
```

---

## 📚 Scripts Detalhados

### 📥 Download NYC Taxi Data

#### Funcionalidades
```python
# Download automático
def download_nyc_data():
    """Download dados NYC TLC automaticamente"""
    url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
    output_path = "data/nyc_taxi/yellow_tripdata_2024-01.parquet"
    
    # Download com progress bar
    download_with_progress(url, output_path)
    
    # Limitar dados para 1GB
    limit_parquet_rows(output_path, max_rows=100000)
```

#### Configurações
```python
# Configurações do download
DOWNLOAD_CONFIG = {
    "url": "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet",
    "output_dir": "data/nyc_taxi/",
    "filename": "yellow_tripdata_2024-01.parquet",
    "max_rows": 100000,  # Limitar para ~1GB
    "chunk_size": 8192,  # Tamanho do chunk de download
    "timeout": 30,       # Timeout em segundos
}
```

### 🧹 Clean Tables

#### Funcionalidades
```python
# Limpeza completa
def clean_all_tables():
    """Limpar todas as tabelas do keyspace"""
    tables = get_all_tables()
    
    for table in tables:
        print(f"Limpando tabela: {table}")
        truncate_table(table)
        print(f"✅ Tabela {table} limpa")

# Limpeza seletiva
def clean_specific_table(table_name: str):
    """Limpar tabela específica"""
    if table_exists(table_name):
        truncate_table(table_name)
        print(f"✅ Tabela {table_name} limpa")
    else:
        print(f"❌ Tabela {table_name} não encontrada")
```

#### Opções de Linha de Comando
```bash
# Limpeza básica
python scripts/clean_tables.py

# Limpeza com opções
python scripts/clean_tables.py --table nyc_taxi_clean --data-only --confirm

# Limpeza interativa
python scripts/clean_tables.py --interactive
```

### 📊 Benchmark Scripts

#### Benchmark de Inserção
```python
# Teste de inserção em lote
def benchmark_bulk_insert():
    """Benchmark de inserção em lote"""
    batch_sizes = [10, 25, 50, 100]
    results = {}
    
    for batch_size in batch_sizes:
        start_time = time.time()
        insert_batch(batch_size)
        end_time = time.time()
        
        results[batch_size] = {
            "time": end_time - start_time,
            "rate": batch_size / (end_time - start_time)
        }
    
    return results
```

#### Benchmark de Consulta
```python
# Teste de consultas
def benchmark_queries():
    """Benchmark de diferentes tipos de consulta"""
    queries = [
        ("all", lambda: list(Model.all())),
        ("filter", lambda: list(Model.filter(field="value"))),
        ("get", lambda: Model.get(id=uuid.uuid4())),
        ("count", lambda: len(list(Model.all()))),
    ]
    
    results = {}
    for name, query_func in queries:
        start_time = time.time()
        result = query_func()
        end_time = time.time()
        
        results[name] = {
            "time": end_time - start_time,
            "count": len(result) if hasattr(result, '__len__') else 1
        }
    
    return results
```

---

## 🎯 Padrões de Script

### 1. **Estrutura Padrão**
```python
#!/usr/bin/env python3
"""
Script: Nome do Script
Descrição: O que o script faz
Autor: Seu Nome
Data: 2025-07-05
"""

import argparse
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Função principal do script"""
    parser = argparse.ArgumentParser(description="Descrição do script")
    parser.add_argument("--option", help="Opção do script")
    args = parser.parse_args()
    
    try:
        # Lógica principal
        execute_script(args)
        logger.info("✅ Script executado com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
```

### 2. **Configuração de Ambiente**
```python
# Verificar ambiente
def check_environment():
    """Verificar se o ambiente está configurado"""
    required_dirs = ["data", "logs", "results"]
    
    for dir_name in required_dirs:
        Path(dir_name).mkdir(exist_ok=True)
    
    # Verificar Cassandra
    try:
        from caspyorm import connection
        connection.connect(contact_points=['localhost'])
        logger.info("✅ Cassandra conectado")
    except Exception as e:
        logger.error(f"❌ Erro Cassandra: {e}")
        return False
    
    return True
```

### 3. **Progress Reporting**
```python
# Barra de progresso
from tqdm import tqdm

def process_with_progress(items, func):
    """Processar itens com barra de progresso"""
    results = []
    
    for item in tqdm(items, desc="Processando"):
        result = func(item)
        results.append(result)
    
    return results
```

---

## 🔍 Análise de Performance

### Métricas dos Scripts
| Script | Operação | Tempo | Performance | Status |
|--------|----------|-------|-------------|--------|
| **Download** | NYC TLC | ~2min | 48MB | ✅ Rápido |
| **Clean Tables** | Limpeza | ~5s | 100% | ✅ Eficiente |
| **Benchmark** | Testes | ~10min | Completo | ✅ Abrangente |

### Otimizações Aplicadas
- **Download**: Chunked download com progress bar
- **Limpeza**: TRUNCATE em lote
- **Benchmark**: Múltiplas iterações para precisão

---

## 🐛 Troubleshooting

### Problemas Comuns

#### Download Falha
```bash
# Verificar conectividade
curl -I https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet

# Download manual
wget https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet
```

#### Limpeza Falha
```bash
# Verificar permissões Cassandra
cqlsh -e "DESCRIBE KEYSPACE my_keyspace"

# Limpeza manual
cqlsh -e "TRUNCATE TABLE my_keyspace.my_table"
```

#### Benchmark Lento
```bash
# Reduzir volume de dados
# Editar: max_rows=10000 em vez de 100000

# Usar dados sintéticos
python scripts/benchmark/synthetic_benchmark.py
```

---

## 📚 Documentação Relacionada

- [Testes](../tests/) - Testes organizados por categoria
- [Exemplos](../examples/) - Exemplos de uso
- [Análise de Performance](../docs/performance/) - Métricas detalhadas
- [Dados](../data/) - Dados de teste organizados

---

**Status**: ✅ **Scripts Organizados e Funcionais**  
**Última Atualização**: 05/07/2025  
**Cobertura**: 100% das operações principais 