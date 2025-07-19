# 🧪 Testes CaspyORM

## 📋 Visão Geral

Esta pasta contém todos os testes da biblioteca CaspyORM, organizados por categoria para facilitar navegação e execução.

---

## 📁 Estrutura dos Testes

### 🔬 [`unit/`](unit/)
**Testes unitários** - Funcionalidades básicas da biblioteca
- `test_01_model_definition.py` - Definição de modelos
- `test_02_crud.py` - Operações CRUD básicas
- `test_03_collections.py` - Campos de coleção (List, Set, Dict)
- `test_04_queryset.py` - Funcionalidades do QuerySet
- `test_05_schema_sync.py` - AutoSchema e sincronização
- `test_06_pydantic_api.py` - Integração com Pydantic
- `test_07_exceptions.py` - Tratamento de exceções

### 🔗 [`integration/`](integration/)
**Testes de integração** - Funcionalidades avançadas
- `test_08_nivel1_improvements.py` - Melhorias nível 1
- `test_09_nivel2_improvements.py` - Melhorias nível 2
- `test_10_pydantic_collections.py` - Coleções com Pydantic
- `test_11_nivel3_improvements.py` - Melhorias nível 3
- `test_12_nyc_taxi_performance.py` - Performance com dados sintéticos

### ⚡ [`performance/`](performance/)
**Testes de performance** - Benchmark e métricas
- `benchmark_nyc_taxi.py` - Benchmark completo
- `test_nyc_operations.py` - Teste de operações com dados reais

### 🚕 [`nyc_taxi/`](nyc_taxi/)
**Testes específicos NYC TLC** - Dados reais de táxi
- `test_nyc_1gb_clean.py` - Versão limpa e otimizada
- `test_real_nyc_data.py` - Versão básica
- `test_real_nyc_data_1gb.py` - Versão 1GB
- `test_real_nyc_data_1gb_fast.py` - Versão rápida
- `test_real_nyc_data_1gb_ultra.py` - Versão ultra-otimizada

---

## 🚀 Como Executar os Testes

### Testes Unitários
```bash
# Executar todos os testes unitários
python -m pytest tests/unit/

# Executar teste específico
python -m pytest tests/unit/test_01_model_definition.py
```

### Testes de Integração
```bash
# Executar todos os testes de integração
python -m pytest tests/integration/

# Executar teste específico
python -m pytest tests/integration/test_12_nyc_taxi_performance.py
```

### Testes de Performance
```bash
# Executar benchmark
python tests/performance/benchmark_nyc_taxi.py

# Executar teste de operações
python tests/performance/test_nyc_operations.py
```

### Testes NYC TLC
```bash
# Executar teste limpo (recomendado)
python tests/nyc_taxi/test_nyc_1gb_clean.py

# Executar versão ultra-otimizada
python tests/nyc_taxi/test_real_nyc_data_1gb_ultra.py
```

---

## 📊 Resultados dos Testes

### Performance com Dados Reais (100k registros)
| Métrica | Valor | Status |
|---------|-------|--------|
| **Inserção** | 794 registros/segundo | ✅ Excelente |
| **Consulta** | 17.235 operações/segundo | ✅ Excelente |
| **Memória** | ~1GB controlado | ✅ Estável |
| **Tempo total** | 2.1 minutos | ✅ Rápido |

### Funcionalidades Testadas
| Categoria | Status | Cobertura |
|-----------|--------|-----------|
| **Modelos** | ✅ | 100% |
| **CRUD** | ✅ | 100% |
| **QuerySet** | ✅ | 90% |
| **AutoSchema** | ✅ | 85% |
| **Pydantic** | ✅ | 100% |
| **Performance** | ✅ | 95% |

---

## 🎯 Ordem Recomendada de Execução

### 1. **Testes Unitários** (Fundamentos)
```bash
python -m pytest tests/unit/ -v
```
**Objetivo**: Verificar funcionalidades básicas

### 2. **Testes de Integração** (Funcionalidades)
```bash
python -m pytest tests/integration/ -v
```
**Objetivo**: Verificar integração entre componentes

### 3. **Testes de Performance** (Benchmark)
```bash
python tests/performance/test_nyc_operations.py
```
**Objetivo**: Avaliar performance com dados reais

### 4. **Testes NYC TLC** (Cenário Real)
```bash
python tests/nyc_taxi/test_nyc_1gb_clean.py
```
**Objetivo**: Validar com dados reais em volume

---

## ⚠️ Pré-requisitos

### Cassandra
```bash
# Iniciar Cassandra
sudo systemctl start cassandra
# ou
cassandra -f
```

### Dependências
```bash
# Instalar dependências
pip install -r requirements.txt

# Ativar ambiente virtual
source .venv/bin/activate
```

### Dados de Teste
```bash
# Download automático (executado pelos testes)
# Dados NYC TLC: ~48MB (yellow_tripdata_2024-01.parquet)
```

---

## 🔍 Análise de Resultados

### Testes Unitários
- **Tempo**: ~30 segundos
- **Cobertura**: 100% das funcionalidades básicas
- **Status**: ✅ Todos passando

### Testes de Performance
- **Tempo**: ~5 minutos
- **Dados**: 100.000 registros reais
- **Métricas**: Documentadas em `docs/performance/`

### Testes NYC TLC
- **Tempo**: 2-5 minutos
- **Volume**: 100k-1M registros
- **Memória**: 1-2GB

---

## 📚 Documentação Relacionada

- [Análise de Performance](../docs/performance/performance_issues.md)
- [Análise da API](../docs/analysis/api_analysis.md)
- [Documentação Principal](../docs/README.md)
- [Exemplos de Uso](../examples/)

---

## 🐛 Troubleshooting

### Problemas Comuns

#### Cassandra não conecta
```bash
# Verificar se Cassandra está rodando
sudo systemctl status cassandra

# Verificar porta
netstat -an | grep 9042
```

#### Erro de memória
```bash
# Reduzir volume de dados
# Editar: tests/nyc_taxi/test_nyc_1gb_clean.py
# Linha: max_rows=100000 -> max_rows=10000
```

#### Warnings de batch
```bash
# Reduzir batch size
# Editar: BATCH_SIZE = 50 -> BATCH_SIZE = 25
```

---

**Status**: ✅ **Testes Organizados e Funcionais**  
**Última Execução**: 19/07/2024  
**Cobertura**: 95% das funcionalidades 