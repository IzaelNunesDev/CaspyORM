# CaspyORM - Suporte Assíncrono e CLI

## 🚀 Novas Funcionalidades

A CaspyORM agora oferece suporte completo a operações assíncronas e uma CLI poderosa para interagir com seus modelos.

## 📋 Índice

1. [API Assíncrona](#api-assíncrona)
2. [CLI (Command Line Interface)](#cli-command-line-interface)
3. [Exemplos Práticos](#exemplos-práticos)
4. [Migração da API Síncrona](#migração-da-api-síncrona)

---

## 🔄 API Assíncrona

### Visão Geral

A CaspyORM agora suporta operações assíncronas usando `async/await`, permitindo melhor performance em aplicações web e melhor utilização de recursos do sistema.

### Conexão Assíncrona

```python
from caspyorm import connection

# Conectar de forma assíncrona
await connection.connect_async(
    contact_points=['localhost'],
    port=9042,
    keyspace='meu_keyspace'
)

# Desconectar
await connection.disconnect_async()
```

### Modelos com Suporte Assíncrono

#### Operações Básicas

```python
from caspyorm import Model, fields
import uuid
from datetime import datetime

class User(Model):
    __table_name__ = "users"
    
    user_id = fields.UUID(primary_key=True)
    username = fields.Text(partition_key=True)
    email = fields.Text(index=True)
    created_at = fields.Timestamp()

# Criar usuário
user = await User.create_async(
    user_id=uuid.uuid4(),
    username="joao_silva",
    email="joao@example.com",
    created_at=datetime.now()
)

# Buscar usuário
user = await User.get_async(user_id=user_id)

# Salvar alterações
await user.save_async()

# Atualizar campos específicos
await user.update_async(email="novo@email.com")

# Deletar usuário
await user.delete_async()
```

#### Consultas Assíncronas

```python
# Buscar todos os usuários
users = await User.all().all_async()

# Filtrar usuários
active_users = await User.filter(is_active=True).all_async()

# Contar registros
count = await User.filter(is_active=True).count_async()

# Verificar existência
exists = await User.filter(email="joao@example.com").exists_async()

# Primeiro resultado
first_user = await User.filter(is_active=True).first_async()

# Iteração assíncrona
async for user in User.filter(is_active=True):
    print(user.username)
```

#### Operações em Lote

```python
# Criar múltiplos usuários
users = [
    User(user_id=uuid.uuid4(), username=f"user_{i}", email=f"user{i}@example.com")
    for i in range(100)
]
created_users = await User.bulk_create_async(users)
```

#### Atualizações de Coleções

```python
# Adicionar tags
await user.update_collection_async('tags', add=['python', 'developer'])

# Remover tags
await user.update_collection_async('tags', remove=['old_tag'])

# Adicionar likes a um post
await post.update_collection_async('likes', add={user_id})
```

### Integração com FastAPI

```python
from fastapi import FastAPI, HTTPException
from caspyorm import connection, Model

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await connection.connect_async(['localhost'], 'meu_keyspace')
    await User.sync_table_async()

@app.on_event("shutdown")
async def shutdown_event():
    await connection.disconnect_async()

@app.post("/users/")
async def create_user(user_data: UserCreate):
    user = await User.create_async(**user_data.dict())
    return user.to_pydantic_model()

@app.get("/users/")
async def list_users():
    users = []
    async for user in User.all():
        users.append(user.to_pydantic_model())
    return users
```

---

## 🖥️ CLI (Command Line Interface)

### Instalação

A CLI está disponível após instalar o projeto:

```bash
pip install -e .
```

### Configuração

Configure a variável de ambiente para apontar para seus modelos:

```bash
export CASPY_MODELS_PATH="meu_projeto.models"
```

### Comandos Disponíveis

#### Informações Gerais

```bash
# Mostrar ajuda
caspy --help

# Mostrar informações da CLI
caspy info

# Mostrar versão
caspy --version
```

#### Listar Modelos

```bash
# Listar todos os modelos disponíveis
caspy models
```

#### Testar Conexão

```bash
# Testar conexão com Cassandra
caspy connect
```

#### Consultas

```bash
# Buscar um usuário específico
caspy user get --filter username=joao_silva

# Listar usuários ativos
caspy user filter --filter is_active=true

# Contar usuários
caspy user count --filter is_active=true

# Verificar se usuário existe
caspy user exists --filter email=joao@example.com

# Listar posts com limite
caspy post filter --filter is_published=true --limit 10

# Buscar posts de um autor
caspy post filter --filter author_id=uuid-do-autor
```

#### Operações de Deleção

```bash
# Deletar usuário (com confirmação)
caspy user delete --filter username=usuario_antigo
```

### Exemplos de Uso

#### Configuração Inicial

```bash
# 1. Configure o path dos modelos
export CASPY_MODELS_PATH="examples.cli_demo"

# 2. Teste a conexão
caspy connect

# 3. Liste os modelos disponíveis
caspy models
```

#### Consultas Interativas

```bash
# Buscar usuário por email
caspy user get --filter email=joao@example.com

# Listar todos os posts publicados
caspy post filter --filter is_published=true

# Contar usuários ativos
caspy user count --filter is_active=true

# Verificar se existe post com título específico
caspy post exists --filter title="Introdução ao CaspyORM"
```

---

## 📚 Exemplos Práticos

### Exemplo Completo de API Assíncrona

```python
# examples/api/main_api_async.py

import uuid
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from caspyorm import Model, fields, connection

# Modelos
class User(Model):
    __table_name__ = "users"
    
    user_id = fields.UUID(primary_key=True)
    username = fields.Text(partition_key=True)
    email = fields.Text(index=True)
    full_name = fields.Text()
    is_active = fields.Boolean(default=True)
    tags = fields.List(fields.Text())
    created_at = fields.Timestamp()

class Post(Model):
    __table_name__ = "posts"
    
    post_id = fields.UUID(primary_key=True)
    title = fields.Text(required=True)
    content = fields.Text()
    author_id = fields.UUID(index=True)
    tags = fields.List(fields.Text())
    likes = fields.Set(fields.UUID())
    is_published = fields.Boolean(default=False)
    created_at = fields.Timestamp()

# API
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await connection.connect_async(['localhost'], 'caspyorm_async_demo')
    User.sync_table()
    Post.sync_table()

@app.on_event("shutdown")
async def shutdown_event():
    await connection.disconnect_async()

@app.post("/users/")
async def create_user(user_data: dict):
    user = await User.create_async(
        user_id=uuid.uuid4(),
        **user_data,
        created_at=datetime.now()
    )
    return user.to_pydantic_model()

@app.get("/users/")
async def list_users():
    users = []
    async for user in User.all():
        users.append(user.to_pydantic_model())
    return users

@app.get("/users/{user_id}")
async def get_user(user_id: uuid.UUID):
    user = await User.get_async(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user.to_pydantic_model()

@app.put("/users/{user_id}/tags")
async def update_user_tags(user_id: uuid.UUID, tags: List[str]):
    user = await User.get_async(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    await user.update_collection_async('tags', add=tags)
    return {"message": "Tags atualizadas com sucesso"}

@app.get("/users/stats/count")
async def get_user_stats():
    total_users = await User.all().count_async()
    active_users = await User.filter(is_active=True).count_async()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users
    }
```

### Exemplo de CLI

```python
# examples/cli_demo.py

import uuid
from datetime import datetime
from caspyorm import Model, fields, connection

class User(Model):
    __table_name__ = "users"
    
    user_id = fields.UUID(primary_key=True)
    username = fields.Text(partition_key=True)
    email = fields.Text(index=True)
    full_name = fields.Text()
    is_active = fields.Boolean(default=True)
    tags = fields.List(fields.Text())
    created_at = fields.Timestamp()

class Post(Model):
    __table_name__ = "posts"
    
    post_id = fields.UUID(primary_key=True)
    title = fields.Text(required=True)
    content = fields.Text()
    author_id = fields.UUID(index=True)
    tags = fields.List(fields.Text())
    likes = fields.Set(fields.UUID())
    is_published = fields.Boolean(default=False)
    created_at = fields.Timestamp()

async def setup_demo_data():
    """Configura dados de demonstração para testar a CLI."""
    await connection.connect_async(['localhost'], 'caspyorm_demo')
    
    # Criar dados de exemplo...
    users = [
        await User.create_async(
            user_id=uuid.uuid4(),
            username="joao_silva",
            email="joao@example.com",
            full_name="João Silva",
            tags=["python", "developer"],
            created_at=datetime.now()
        ),
        # ... mais usuários
    ]
    
    print("✅ Dados de demonstração criados!")
    print("\n📋 Exemplos de comandos CLI:")
    print("   export CASPY_MODELS_PATH='examples.cli_demo'")
    print("   caspy models")
    print("   caspy user get --filter username=joao_silva")
    print("   caspy user filter --filter is_active=true")

if __name__ == "__main__":
    import asyncio
    asyncio.run(setup_demo_data())
```

---

## 🔄 Migração da API Síncrona

### Comparação de APIs

| Operação | Síncrona | Assíncrona |
|----------|----------|------------|
| Conexão | `connection.connect()` | `await connection.connect_async()` |
| Criar | `User.create()` | `await User.create_async()` |
| Buscar | `User.get()` | `await User.get_async()` |
| Salvar | `user.save()` | `await user.save_async()` |
| Atualizar | `user.update()` | `await user.update_async()` |
| Deletar | `user.delete()` | `await user.delete_async()` |
| Listar | `User.all().all()` | `await User.all().all_async()` |
| Filtrar | `User.filter().all()` | `await User.filter().all_async()` |
| Contar | `User.filter().count()` | `await User.filter().count_async()` |
| Iterar | `for user in User.all()` | `async for user in User.all()` |

### Migração Gradual

A API síncrona continua funcionando, permitindo migração gradual:

```python
# Código existente (continua funcionando)
user = User.create(username="joao", email="joao@example.com")

# Novo código assíncrono
user = await User.create_async(username="joao", email="joao@example.com")
```

### Benefícios da API Assíncrona

1. **Performance**: Melhor utilização de recursos do sistema
2. **Escalabilidade**: Suporte a mais conexões simultâneas
3. **Integração**: Compatível com FastAPI e outras frameworks assíncronas
4. **Flexibilidade**: Permite operações não-bloqueantes

---

## 🎯 Próximos Passos

1. **Implementar TODOs**: Completar implementações assíncronas pendentes
2. **Testes**: Adicionar testes para funcionalidades assíncronas
3. **Documentação**: Expandir exemplos e casos de uso
4. **Performance**: Otimizar operações em lote assíncronas
5. **CLI Avançada**: Adicionar mais comandos e funcionalidades

---

## 📖 Referências

- [Documentação do cassandra-driver](https://docs.datastax.com/en/developer/python-driver/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Rich Documentation](https://rich.readthedocs.io/) 