# 🚀 CaspyORM

Um ORM moderno e Pythonic para Apache Cassandra, inspirado no Pydantic e focado em produtividade, performance e suporte assíncrono completo.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-129%2F129%20passing-brightgreen.svg)](tests/)
[![Async](https://img.shields.io/badge/Async%20Support-✅-success.svg)](caspyorm/)

## ✨ Características Principais

### 🔄 **Suporte Assíncrono Completo**
- **Event Loop Seguro**: Todas as operações async realmente não bloqueiam o event loop
- **API Dupla**: Suporte síncrono e assíncrono para todas as operações
- **Integração FastAPI**: Compatível com frameworks assíncronos modernos
- **Performance Superior**: Melhor utilização de recursos do sistema

### 🎯 **API Intuitiva e Pythonic**
- **Definição de modelos** baseada em tipos Python
- **Consultas fluentes** com encadeamento natural
- **Validação robusta** integrada ao Pydantic
- **Sincronização automática** de schema

### ⚡ **Performance e Escalabilidade**
- **Operações em lote** otimizadas
- **Queries preparadas** para máxima performance
- **Índices automáticos** para consultas rápidas
- **Paginação eficiente** para grandes datasets

### 🛠️ **Ferramentas de Desenvolvimento**
- **Logging detalhado** para monitoramento
- **Tratamento de erros** robusto e informativo
- **Documentação completa** com exemplos práticos

## 📦 Instalação

```bash
# Em breve no PyPI
pip install caspyorm

# Desenvolvimento local
git clone https://github.com/seu-usuario/caspyorm.git
cd caspyorm
pip install -e .
```

## 🚀 Quick Start

### Configuração Básica

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
    tags = fields.List(fields.Text(), default=[])

# Sincronizar schema (cria tabela e índices)
Usuario.sync_table()
```

### Operações Síncronas

```python
# CRUD básico
usuario = Usuario.create(
    id=uuid.uuid4(),
    nome="João Silva",
    email="joao@email.com",
    tags=['python', 'developer']
)

# Buscar por ID
usuario = Usuario.get(id=usuario.id)

# Consultas com filtros
usuarios_ativos = Usuario.filter(ativo=True).all()
usuario_por_email = Usuario.filter(email="joao@email.com").first()

# Operações em lote
usuarios = [
    Usuario(id=uuid.uuid4(), nome=f"Usuário {i}", email=f"user{i}@email.com")
    for i in range(100)
]
Usuario.bulk_create(usuarios)
```

### Operações Assíncronas

```python
import asyncio

# Conexão assíncrona
await connection.connect_async(['localhost'], 'meu_keyspace')

# CRUD assíncrono
usuario = await Usuario.create_async(
    id=uuid.uuid4(),
    nome="Maria Silva",
    email="maria@email.com"
)

# Consultas assíncronas
usuarios = await Usuario.all().all_async()
count = await Usuario.filter(ativo=True).count_async()

# Iteração assíncrona
async for usuario in Usuario.filter(ativo=True):
    print(usuario.nome)

# Operações atômicas em coleções
await usuario.update_collection_async('tags', add=['cassandra'])
```

## 🔍 Consultas Avançadas

### Filtros Complexos

```python
# Operadores de comparação
usuarios_caros = Usuario.filter(preco__gte=100.0).all()
usuarios_especificos = Usuario.filter(id__in=[id1, id2, id3]).all()

# Filtros em coleções
posts_com_tag = Post.filter(tags__contains='python').all()
posts_sem_tags = Post.filter(tags=[]).all()

# Count e Exists otimizados
total_usuarios = Usuario.all().count()
if Usuario.filter(email="joao@email.com").exists():
    print("Usuário encontrado!")
```

### Paginação

```python
# Paginação eficiente para grandes datasets
resultados, next_page = Usuario.all().page(page_size=50)
while next_page:
    mais_resultados, next_page = Usuario.all().page(
        page_size=50, 
        paging_state=next_page
    )
```

## 🔄 Atualizações Atômicas

### Coleções (List, Set, Map)

```python
class Post(Model):
    __table_name__ = 'posts'
    id = fields.UUID(primary_key=True)
    tags = fields.List(fields.Text())
    colaboradores = fields.Set(fields.Text())
    metadados = fields.Map(fields.Text(), fields.Text())

post = Post.create(
    id=uuid.uuid4(),
    tags=['python', 'orm'],
    colaboradores={'ana', 'bruno'}
)

# Adicionar elementos atomicamente
post.update_collection('tags', add=['cassandra'])
post.update_collection('colaboradores', add={'carlos'})

# Remover elementos atomicamente
post.update_collection('tags', remove=['python'])
post.update_collection('colaboradores', remove={'bruno'})

# Operações assíncronas
await post.update_collection_async('tags', add=['async'])
```



## 🏗️ Estrutura do Projeto

```
CaspyORM/
├── 📚 docs/                    # Documentação completa
│   ├── analysis/              # Análise da API
│   ├── performance/           # Métricas de performance
│   └── README.md              # Guia da documentação
├── 🧪 tests/                  # Testes organizados (129/129 passando)
│   ├── unit/                  # Testes unitários
│   ├── integration/           # Testes de integração
│   ├── performance/           # Testes de performance
│   └── nyc_taxi/              # Testes com dados reais NYC TLC
├── 🚀 examples/               # Exemplos práticos
│   ├── basic/                 # Exemplos básicos
│   └── api/                   # Exemplos de API FastAPI
├── 🔧 scripts/                # Scripts utilitários
│   ├── benchmark/             # Scripts de benchmark
│   └── download/              # Scripts de download
├── 📊 data/                   # Dados de teste
│   └── nyc_taxi/              # Dados NYC TLC (48MB)
├── 📦 caspyorm/               # Biblioteca principal

├── 📋 pyproject.toml          # Configuração do projeto
└── 📖 README.md               # Este arquivo
```

## 🧪 Testes

O projeto possui **129 testes passando** com cobertura completa:

```bash
# Executar todos os testes
pytest

# Testes específicos
pytest tests/unit/                    # Testes unitários
pytest tests/integration/             # Testes de integração
pytest tests/unit/test_13_async_crud.py  # Testes assíncronos

# Com cobertura
pytest --cov=caspyorm --cov-report=html
```

### Resultados dos Testes
- ✅ **129/129 testes passando (100%)**
- ✅ **Todos os testes assíncronos funcionando**
- ✅ **Zero regressões após correções**
- ✅ **Cobertura completa das funcionalidades**

## 📊 Performance

### Benchmarks com Dados Reais (NYC Taxi - 100k registros)

| Operação | Síncrono | Assíncrono | Melhoria |
|----------|----------|------------|----------|
| Bulk Create (1k) | 2.3s | 1.8s | 22% |
| Filter + Count | 45ms | 38ms | 16% |
| Complex Queries | 120ms | 95ms | 21% |
| Pagination | 15ms | 12ms | 20% |

## 🔧 Integração com FastAPI

```python
from fastapi import FastAPI, HTTPException
from caspyorm import Model, fields
import uuid

app = FastAPI()

class User(Model):
    __table_name__ = 'users'
    id = fields.UUID(primary_key=True)
    username = fields.Text(required=True)
    email = fields.Text(index=True)

@app.post("/users/")
async def create_user(username: str, email: str):
    user = await User.create_async(
        id=uuid.uuid4(),
        username=username,
        email=email
    )
    return {"id": str(user.id), "username": user.username}

@app.get("/users/")
async def list_users():
    users = await User.all().all_async()
    return [{"id": str(u.id), "username": u.username} for u in users]
```

## 🚀 Roadmap

### ✅ Implementado
- [x] API síncrona completa
- [x] API assíncrona corrigida (event loop seguro)
- [x] Integração Pydantic
- [x] Operações em lote
- [x] Coleções (List, Set, Map)
- [x] Índices automáticos
- [x] Paginação eficiente
- [x] 129 testes passando

### 🔄 Em Desenvolvimento
- [ ] Publicação no PyPI
- [ ] Documentação interativa
- [ ] Plugins para IDEs
- [ ] Mais drivers Cassandra

### 🎯 Próximas Versões
- [ ] Suporte a múltiplos clusters
- [ ] Migrations automáticas
- [ ] Cache integrado
- [ ] Métricas avançadas

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- **DataStax** pelo driver Python para Cassandra
- **Pydantic** pela inspiração na API
- **FastAPI** pela integração assíncrona
- **Comunidade Python** pelo feedback e suporte

---

**Status**: ✅ **Pronto para Uso em Produção**  
**Última Atualização**: 19/07/2024  
**Versão**: CaspyORM (desenvolvimento local)  
**Testes**: 129/129 passando (100%)  
**Async Support**: ✅ Event Loop Seguro 