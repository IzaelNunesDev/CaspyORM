# Guia Rápido - CaspyORM

Este guia rápido te ajudará a começar com CaspyORM em poucos minutos.

## Instalação

```bash
pip install caspyorm
```

## Configuração Inicial

### 1. Conectar ao Cassandra

```python
from caspyorm import connection

# Conectar ao Cassandra
connection.connect(
    contact_points=['localhost'],
    keyspace='my_keyspace'
)
```

### 2. Definir um Modelo

```python
from caspyorm import Model
from caspyorm.fields import Text, Integer, UUID
import uuid

class User(Model):
    __table_name__ = "users"
    
    id = UUID(primary_key=True)
    name = Text(required=True)
    email = Text(index=True)
    age = Integer()
```

### 3. Sincronizar a Tabela

```python
# Criar a tabela no Cassandra
User.sync_table()
```

## Operações Básicas

### Criar um Usuário

```python
# Criar usuário
user = User.create(
    id=uuid.uuid4(),
    name="João Silva",
    email="joao@example.com",
    age=30
)
```

### Buscar Usuários

```python
# Buscar por ID
user = User.get(id=user.id)

# Buscar por email
user = User.get(email="joao@example.com")

# Buscar múltiplos usuários
users = User.filter(age__gte=25).all()

# Buscar com limite
young_users = User.filter(age__lt=30).limit(10).all()
```

### Atualizar um Usuário

```python
# Atualizar campos
user.update(name="João Silva Santos", age=31)

# Ou atualizar diretamente
user.name = "João Silva Santos"
user.age = 31
user.save()
```

### Deletar um Usuário

```python
# Deletar por instância
user.delete()

# Deletar por filtro
User.filter(email="joao@example.com").delete()
```

## Operações Assíncronas

CaspyORM suporta operações assíncronas nativas:

```python
import asyncio

async def main():
    # Criar usuário de forma assíncrona
    user = await User.create_async(
        id=uuid.uuid4(),
        name="Maria Santos",
        email="maria@example.com",
        age=28
    )
    
    # Buscar usuário
    found_user = await User.get_async(email="maria@example.com")
    
    # Atualizar
    await user.update_async(age=29)
    
    # Deletar
    await user.delete_async()

# Executar
asyncio.run(main())
```

## Paginação

```python
# Primeira página
users, next_page = User.filter(age__gte=25).page(page_size=10)

# Próxima página
if next_page:
    more_users, next_page = User.filter(age__gte=25).page(
        page_size=10, 
        paging_state=next_page
    )
```

## Operações em Lote

```python
# Criar múltiplos usuários
users_data = [
    {"id": uuid.uuid4(), "name": "User 1", "email": "user1@example.com"},
    {"id": uuid.uuid4(), "name": "User 2", "email": "user2@example.com"},
    {"id": uuid.uuid4(), "name": "User 3", "email": "user3@example.com"},
]

users = User.bulk_create([User(**data) for data in users_data])
```

## Modelos Dinâmicos

Você pode criar modelos em tempo de execução:

```python
# Criar modelo dinamicamente
ProductModel = Model.create_model(
    name="Product",
    fields={
        "id": UUID(primary_key=True),
        "name": Text(required=True),
        "price": Float(),
        "category": Text(index=True),
        "tags": List(Text())
    }
)

# Usar normalmente
product = ProductModel(
    id=uuid.uuid4(),
    name="Laptop",
    price=999.99,
    category="Electronics",
    tags=["computer", "portable"]
)
await product.save_async()
```

## Integração com FastAPI

```python
from fastapi import FastAPI, Depends
from caspyorm.contrib.fastapi import get_async_session, handle_caspyorm_errors

app = FastAPI()

@app.get("/users/{user_id}")
@handle_caspyorm_errors
async def get_user(user_id: str, session = Depends(get_async_session)):
    user = await User.get_async(id=user_id)
    return user.model_dump()

@app.post("/users")
@handle_caspyorm_errors
async def create_user(user_data: dict, session = Depends(get_async_session)):
    user = await User.create_async(**user_data)
    return user.model_dump()
```

## Próximos Passos

- Leia a [Definição de Modelos](models/definition.md) para detalhes sobre campos e validação
- Explore as [Operações CRUD](queries/crud.md) para operações mais avançadas
- Veja as [Operações Assíncronas](async.md) para melhor performance
- Consulte a [API Reference](api/model.md) para documentação completa 