# CaspyORM

Um ORM moderno e Pythonic para Apache Cassandra, inspirado no Pydantic e focado em produtividade e performance.

## 📁 Estrutura do Projeto

```
Cassandra_teste/
├── 📚 docs/                    # Documentação completa
│   ├── analysis/              # Análise da API
│   ├── performance/           # Métricas de performance
│   └── README.md              # Guia da documentação
├── 🧪 tests/                  # Testes organizados
│   ├── unit/                  # Testes unitários
│   ├── integration/           # Testes de integração
│   ├── performance/           # Testes de performance
│   ├── nyc_taxi/              # Testes com dados reais NYC TLC
│   └── README.md              # Guia dos testes
├── 🚀 examples/               # Exemplos práticos
│   ├── basic/                 # Exemplos básicos
│   ├── nyc_taxi/              # Exemplos com dados reais
│   ├── api/                   # Exemplos de API
│   └── README.md              # Guia dos exemplos
├── 🔧 scripts/                # Scripts utilitários
│   ├── benchmark/             # Scripts de benchmark
│   ├── download/              # Scripts de download
│   └── README.md              # Guia dos scripts
├── 📊 data/                   # Dados de teste
│   ├── nyc_taxi/              # Dados NYC TLC
│   └── README.md              # Guia dos dados
├── 📦 caspyorm/               # Biblioteca principal
├── 📋 pyproject.toml          # Configuração do projeto
└── 📖 README.md               # Este arquivo
```

## 🚀 Funcionalidades Implementadas

### ✨ **Core Features**
*   **Definição de modelos intuitiva** e baseada em tipos Python
*   **Sincronização automática de schema** com criação de tabelas e índices
*   **Consultas fluentes e encadeadas** (`filter`, `get`, `all`, `first`)
*   **Validação de dados robusta** e customizável
*   **Suporte completo a coleções** (List, Set, Map) com tipos tipados

### 🔍 **Consultas Avançadas**
*   **Count otimizado** - `SELECT COUNT(*)` em vez de buscar todos os dados
*   **Exists otimizado** - `SELECT <pk> LIMIT 1` para verificação de existência
*   **Filtros complexos** - `exact`, `gt`, `gte`, `lt`, `lte`, `in`
*   **Ordenação** - `order_by()` com suporte a ASC/DESC
*   **Paginação** - `page()` com paging_state para grandes datasets
*   **Warnings inteligentes** para campos não indexados

### ⚡ **Performance & Escalabilidade**
*   **Operações em lote** - `bulk_create()` com UNLOGGED BATCH
*   **Atualizações atômicas** - `update_collection()` para List/Set
*   **Índices secundários automáticos** - Criação e sincronização
*   **Queries preparadas** - Reutilização de statements para performance

### 🔧 **Integração & Utilitários**
*   **Integração Pydantic** - `as_pydantic()` e `to_pydantic_model()`
*   **Logging detalhado** - Debug e monitoramento de queries
*   **Tratamento de exceções** - Mensagens claras e específicas
*   **Compatibilidade FastAPI** - Modelos prontos para APIs web

## 📦 Instalação

```bash
# Em breve
pip install caspyorm
```

## 🎯 Exemplo de Uso Básico

```python
from caspyorm import Model, fields, connection
import uuid

# Configurar conexão
connection.setup(['localhost'], 'meu_keyspace')

class Usuario(Model):
    __table_name__ = 'usuarios'
    id = fields.UUID(primary_key=True)
    nome = fields.Text(required=True)
    email = fields.Text(index=True)
    ativo = fields.Boolean(default=True)

# Sincronizar schema (cria tabela e índices)
Usuario.sync_table()

# CRUD básico
usuario = Usuario.create(
    id=uuid.uuid4(),
    nome="João Silva",
    email="joao@email.com"
)

# Buscar por ID
usuario = Usuario.get(id=usuario.id)

# Consultas com filtros
usuarios_ativos = Usuario.filter(ativo=True).all()
usuario_por_email = Usuario.filter(email="joao@email.com").first()
```

## 🔍 Consultas Avançadas

### Count e Exists Otimizados

```python
# Count otimizado - usa SELECT COUNT(*) internamente
total_usuarios = Usuario.all().count()
usuarios_ativos = Usuario.filter(ativo=True).count()

# Exists otimizado - usa SELECT <pk> LIMIT 1
if Usuario.filter(email="joao@email.com").exists():
    print("Usuário encontrado!")

# Filtros complexos
usuarios_caros = Usuario.filter(preco__gte=100.0).count()
usuarios_especificos = Usuario.filter(id__in=[id1, id2, id3]).all()
```

### Paginação

```python
# Paginação eficiente para grandes datasets
resultados, next_page = Usuario.all().page(page_size=50)
while next_page:
    mais_resultados, next_page = Usuario.all().page(page_size=50, paging_state=next_page)
```

## ⚡ Operações em Lote

### Bulk Create

```python
# Criar múltiplos registros de uma vez (muito mais rápido)
usuarios = [
    Usuario(id=uuid.uuid4(), nome=f"Usuário {i}", email=f"user{i}@email.com")
    for i in range(1000)
]

# Inserção em lote com UNLOGGED BATCH
Usuario.bulk_create(usuarios)
```

## 🔄 Atualizações Atômicas

### Update de Coleções

```python
class Post(Model):
    __table_name__ = 'posts'
    id = fields.UUID(primary_key=True)
    tags = fields.List(fields.Text())
    colaboradores = fields.Set(fields.Text())

post = Post.create(
    id=uuid.uuid4(),
    tags=['python', 'orm'],
    colaboradores={'ana', 'bruno'}
)

# Adicionar tags atomicamente (sem recarregar o objeto)
post.update_collection('tags', add=['cassandra'])

# Remover colaboradores atomicamente
post.update_collection('colaboradores', remove={'bruno'})
```

## 📊 Sincronização de Schema

### Criação Automática de Tabelas e Índices

```python
class Produto(Model):
    __table_name__ = 'produtos'
    id = fields.UUID(primary_key=True)
    nome = fields.Text(required=True)
    categoria = fields.Text(index=True)  # Índice criado automaticamente
    preco = fields.Float(index=True)     # Índice criado automaticamente
    ativo = fields.Boolean()             # Sem índice

# Cria tabela e índices automaticamente
Produto.sync_table()

# Adicionar novo campo posteriormente
class Produto(Model):
    # ... campos anteriores ...
    descricao = fields.Text()  # Novo campo

# sync_table() adiciona o novo campo sem perder dados
Produto.sync_table()
```

## 🏗️ Campos de Coleção (List, Set, Map)

### List

```python
class Post(Model):
    id = fields.UUID(primary_key=True)
    titulo = fields.Text(required=True)
    tags = fields.List(fields.Text())  # Lista de strings

post = Post.create(
    id=uuid.uuid4(),
    titulo="Exemplo com listas",
    tags=["python", "orm", "cassandra"]
)
```

### Set

```python
class Artigo(Model):
    id = fields.UUID(primary_key=True)
    tags = fields.Set(fields.Text())  # Conjunto de strings

artigo = Artigo.create(
    id=uuid.uuid4(),
    tags={"python", "cassandra", "orm"}
)
```

### Map

```python
class Config(Model):
    id = fields.UUID(primary_key=True)
    settings = fields.Map(fields.Text(), fields.Text())  # Map<string, string>

config = Config.create(
    id=uuid.uuid4(),
    settings={
        "theme": "dark",
        "language": "pt-BR",
        "timezone": "America/Sao_Paulo"
    }
)
```

## 🧪 Testes e Validação

### Executar Testes

```bash
# Testes unitários
python -m pytest tests/unit/

# Testes de integração
python -m pytest tests/integration/

# Testes de performance
python tests/performance/test_nyc_operations.py

# Testes com dados reais NYC TLC
python tests/nyc_taxi/test_nyc_1gb_clean.py
```

### Performance com Dados Reais

| Métrica | Valor | Status |
|---------|-------|--------|
| **Inserção** | 794 registros/segundo | ✅ Excelente |
| **Consulta** | 17.235 operações/segundo | ✅ Excelente |
| **Memória** | ~1GB para 100k registros | ✅ Controlado |
| **Escalabilidade** | Linear com volume | ✅ Boa |

## 📚 Documentação

### 📖 Guias Principais
- **[Documentação Completa](docs/README.md)** - Visão geral da documentação
- **[Análise de Performance](docs/performance/performance_issues.md)** - Métricas detalhadas
- **[Análise da API](docs/analysis/api_analysis.md)** - Estudo da API

### 🚀 Exemplos Práticos
- **[Exemplos Básicos](examples/basic/)** - Funcionalidades fundamentais
- **[Exemplos NYC Taxi](examples/nyc_taxi/)** - Dados reais de performance
- **[Exemplos de API](examples/api/)** - Integração com FastAPI

### 🔧 Scripts Utilitários
- **[Scripts de Download](scripts/download/)** - Obtenção de dados
- **[Scripts de Benchmark](scripts/benchmark/)** - Testes de performance
- **[Scripts de Limpeza](scripts/clean_tables.py)** - Manutenção

## 🎯 Casos de Uso

### ✅ **Ideal Para**
- Aplicações que precisam de alta performance de escrita
- Sistemas que lidam com grandes volumes de dados
- APIs que requerem baixa latência
- Projetos que precisam de escalabilidade horizontal

### ⚠️ **Considerações**
- API diferente do Django ORM (curva de aprendizado)
- Consultas complexas requerem processamento em Python
- Design de schema cuidadoso necessário
- Limitações fundamentais do Cassandra

## 🔗 Links Úteis

- **[Testes Organizados](tests/README.md)** - Guia completo dos testes
- **[Exemplos Práticos](examples/README.md)** - Exemplos de uso
- **[Scripts Utilitários](scripts/README.md)** - Scripts de suporte
- **[Dados de Teste](data/README.md)** - Dados organizados

## 📈 Status do Projeto

### ✅ **Funcionalidades Implementadas**
- [x] Definição de modelos com tipos Python
- [x] Sincronização automática de schema
- [x] Operações CRUD completas
- [x] Consultas com filtros e ordenação
- [x] Operações em lote otimizadas
- [x] Suporte a coleções (List, Set, Map)
- [x] Integração com Pydantic
- [x] Testes com dados reais NYC TLC
- [x] Performance validada (794 inserções/s, 17k consultas/s)

### 🚀 **Próximos Passos**
- [ ] Documentação da API completa
- [ ] Guia de migração do Django ORM
- [ ] Exemplos de uso em produção
- [ ] Otimizações adicionais de performance

---

**Status**: ✅ **Pronto para Uso em Produção**  
**Última Atualização**: 05/07/2025  
**Versão**: CaspyORM (desenvolvimento local) 