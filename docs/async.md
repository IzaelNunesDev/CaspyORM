# Operações Assíncronas

CaspyORM oferece suporte nativo a operações assíncronas, permitindo melhor performance e escalabilidade em aplicações modernas.

## Por que Operações Assíncronas?

- **Melhor Performance**: Não bloqueia o event loop durante operações de I/O
- **Escalabilidade**: Permite lidar com mais conexões simultâneas
- **Integração Moderna**: Compatível com FastAPI, aiohttp e outros frameworks assíncronos
- **Eficiência de Recursos**: Menor uso de threads e memória

## Configuração

### Conectar Assincronamente

```python
from caspyorm import connection

# Conectar ao Cassandra de forma assíncrona
await connection.connect_async(
    contact_points=['localhost'],
    keyspace='my_keyspace'
)
```

### Verificar Conexão

```python
# Verificar se a conexão assíncrona está ativa
if connection.is_async_connected():
    print("Conexão assíncrona ativa")
```

## Operações Básicas

### Criar Registros

```python
import asyncio
import uuid
from caspyorm import Model
from caspyorm.fields import Text, Integer, UUID

class User(Model):
    __table_name__ = "users"
    
    id = UUID(primary_key=True)
    name = Text(required=True)
    email = Text(index=True)
    age = Integer()

async def create_user():
    user = await User.create_async(
        id=uuid.uuid4(),
        name="João Silva",
        email="joao@example.com",
        age=30
    )
    return user

# Executar
user = asyncio.run(create_user())
```

### Buscar Registros

```python
async def get_user_by_email(email):
    user = await User.get_async(email=email)
    return user

async def get_users_by_age(min_age):
    users = await User.filter(age__gte=min_age).all_async()
    return users

# Executar
user = asyncio.run(get_user_by_email("joao@example.com"))
young_users = asyncio.run(get_users_by_age(25))
```

### Atualizar Registros

```python
async def update_user_age(user_id, new_age):
    user = await User.get_async(id=user_id)
    if user:
        await user.update_async(age=new_age)
    return user

async def update_user_fields(user_id, **fields):
    user = await User.get_async(id=user_id)
    if user:
        await user.update_async(**fields)
    return user
```

### Deletar Registros

```python
async def delete_user(user_id):
    user = await User.get_async(id=user_id)
    if user:
        await user.delete_async()
        return True
    return False

async def delete_inactive_users():
    count = await User.filter(is_active=False).delete_async()
    return count
```

## Operações em Lote

### Criar Múltiplos Registros

```python
async def create_multiple_users(users_data):
    users = await User.bulk_create_async([
        User(**data) for data in users_data
    ])
    return users

# Exemplo de uso
users_data = [
    {"id": uuid.uuid4(), "name": "User 1", "email": "user1@example.com", "age": 25},
    {"id": uuid.uuid4(), "name": "User 2", "email": "user2@example.com", "age": 30},
    {"id": uuid.uuid4(), "name": "User 3", "email": "user3@example.com", "age": 35},
]

users = asyncio.run(create_multiple_users(users_data))
```

### Atualizar Múltiplos Registros

```python
async def update_all_active_users():
    users = await User.filter(is_active=True).all_async()
    
    # Atualizar todos os usuários ativos
    for user in users:
        await user.update_async(last_login=datetime.now())
    
    return len(users)
```

## Queries Avançadas

### Filtros Complexos

```python
async def get_users_by_criteria():
    # Usuários jovens e ativos
    young_active = await User.filter(
        age__lt=30, 
        is_active=True
    ).all_async()
    
    # Usuários com email específico ou idade alta
    from caspyorm import Q
    special_users = await User.filter(
        Q(email__contains="@gmail.com") | Q(age__gt=50)
    ).all_async()
    
    return young_active, special_users
```

### Ordenação e Limites

```python
async def get_recent_users(limit=10):
    users = await User.filter().order_by("-created_at").limit(limit).all_async()
    return users

async def get_users_by_name():
    users = await User.filter().order_by("name").all_async()
    return users
```

### Paginação

```python
async def get_users_paginated(page_size=10):
    users, next_page = await User.filter().page_async(page_size=page_size)
    return users, next_page

async def get_all_users_paginated():
    all_users = []
    page_size = 50
    next_page = None
    
    while True:
        users, next_page = await User.filter().page_async(
            page_size=page_size, 
            paging_state=next_page
        )
        all_users.extend(users)
        
        if not next_page:
            break
    
    return all_users
```

### Contagem e Existência

```python
async def get_user_statistics():
    total_users = await User.count_async()
    active_users = await User.filter(is_active=True).count_async()
    young_users = await User.filter(age__lt=30).count_async()
    
    return {
        "total": total_users,
        "active": active_users,
        "young": young_users
    }

async def check_user_exists(email):
    exists = await User.filter(email=email).exists_async()
    return exists
```

## Transações Assíncronas

### Transações Simples

```python
from caspyorm import transaction_async

async def create_user_with_profile():
    async with transaction_async():
        # Criar usuário
        user = await User.create_async(
            id=uuid.uuid4(),
            name="João Silva",
            email="joao@example.com"
        )
        
        # Criar perfil
        profile = await Profile.create_async(
            user_id=user.id,
            bio="Desenvolvedor Python"
        )
        
        # Se algo falhar, tudo é revertido
        return user, profile
```

### Transações com Rollback

```python
async def safe_user_update(user_id, new_data):
    try:
        async with transaction_async():
            user = await User.get_async(id=user_id)
            if not user:
                raise ValueError("Usuário não encontrado")
            
            await user.update_async(**new_data)
            
            # Validação adicional
            if user.age < 0:
                raise ValueError("Idade inválida")
            
            return user
            
    except Exception as e:
        print(f"Erro na transação: {e}")
        return None
```

## Integração com FastAPI

### Endpoints Assíncronos

```python
from fastapi import FastAPI, Depends
from caspyorm.contrib.fastapi import get_async_session, handle_caspyorm_errors

app = FastAPI()

@app.get("/users/{user_id}")
@handle_caspyorm_errors
async def get_user(user_id: str, session = Depends(get_async_session)):
    user = await User.get_async(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user.model_dump()

@app.post("/users")
@handle_caspyorm_errors
async def create_user(user_data: dict, session = Depends(get_async_session)):
    user = await User.create_async(**user_data)
    return user.model_dump()

@app.put("/users/{user_id}")
@handle_caspyorm_errors
async def update_user(user_id: str, user_data: dict, session = Depends(get_async_session)):
    user = await User.get_async(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    await user.update_async(**user_data)
    return user.model_dump()

@app.delete("/users/{user_id}")
@handle_caspyorm_errors
async def delete_user(user_id: str, session = Depends(get_async_session)):
    user = await User.get_async(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    await user.delete_async()
    return {"message": "Usuário deletado com sucesso"}
```

### Listagem com Paginação

```python
@app.get("/users")
@handle_caspyorm_errors
async def list_users(
    page: int = 1,
    page_size: int = 10,
    session = Depends(get_async_session)
):
    offset = (page - 1) * page_size
    
    users, next_page = await User.filter().page_async(
        page_size=page_size,
        paging_state=offset
    )
    
    return {
        "users": [user.model_dump() for user in users],
        "next_page": next_page is not None,
        "page": page,
        "page_size": page_size
    }
```

## Tratamento de Erros

### Capturar Exceções Específicas

```python
from caspyorm.exceptions import ValidationError, ObjectNotFound, ConnectionError

async def safe_user_operation(user_id):
    try:
        user = await User.get_async(id=user_id)
        await user.update_async(age=30)
        return user
        
    except ObjectNotFound:
        print(f"Usuário {user_id} não encontrado")
        return None
        
    except ValidationError as e:
        print(f"Erro de validação: {e}")
        return None
        
    except ConnectionError:
        print("Erro de conexão com o banco")
        return None
        
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return None
```

### Retry com Backoff

```python
import asyncio
from caspyorm.exceptions import ConnectionError

async def retry_operation(operation, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await operation()
        except ConnectionError:
            if attempt == max_retries - 1:
                raise
            
            # Backoff exponencial
            wait_time = 2 ** attempt
            await asyncio.sleep(wait_time)
    
    raise Exception("Máximo de tentativas excedido")

# Uso
async def get_user_with_retry(user_id):
    return await retry_operation(
        lambda: User.get_async(id=user_id)
    )
```

## Performance e Otimização

### Executar Operações em Paralelo

```python
async def get_multiple_users(user_ids):
    # Executar todas as buscas em paralelo
    tasks = [User.get_async(id=user_id) for user_id in user_ids]
    users = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filtrar resultados válidos
    valid_users = [user for user in users if not isinstance(user, Exception)]
    return valid_users
```

### Batch Operations

```python
async def process_users_in_batches(user_ids, batch_size=100):
    results = []
    
    for i in range(0, len(user_ids), batch_size):
        batch = user_ids[i:i + batch_size]
        
        # Processar lote em paralelo
        tasks = [User.get_async(id=user_id) for user_id in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        results.extend(batch_results)
    
    return results
```

## Exemplos Completos

### Sistema de Notificações

```python
class Notification(Model):
    __table_name__ = "notifications"
    
    id = UUID(primary_key=True)
    user_id = UUID(index=True)
    message = Text()
    read = Boolean(default=False)
    created_at = Timestamp(auto_now_add=True)

async def send_notification_to_users(user_ids, message):
    notifications = []
    
    for user_id in user_ids:
        notification = await Notification.create_async(
            id=uuid.uuid4(),
            user_id=user_id,
            message=message
        )
        notifications.append(notification)
    
    return notifications

async def get_unread_notifications(user_id):
    notifications = await Notification.filter(
        user_id=user_id,
        read=False
    ).order_by("-created_at").all_async()
    
    return notifications

async def mark_notifications_as_read(notification_ids):
    for notification_id in notification_ids:
        notification = await Notification.get_async(id=notification_id)
        if notification:
            await notification.update_async(read=True)
```

### Sistema de Cache

```python
class CacheEntry(Model):
    __table_name__ = "cache"
    
    key = Text(primary_key=True)
    value = Text()
    expires_at = Timestamp()

async def get_cached_value(key):
    entry = await CacheEntry.get_async(key=key)
    
    if entry and entry.expires_at > datetime.now():
        return entry.value
    
    return None

async def set_cached_value(key, value, ttl_seconds=3600):
    expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
    
    await CacheEntry.create_async(
        key=key,
        value=value,
        expires_at=expires_at
    )

async def cleanup_expired_cache():
    expired_entries = await CacheEntry.filter(
        expires_at__lt=datetime.now()
    ).all_async()
    
    for entry in expired_entries:
        await entry.delete_async()
    
    return len(expired_entries)
```

## Próximos Passos

- Veja as [Operações CRUD](queries/crud.md) para operações síncronas
- Explore a [Integração com FastAPI](fastapi.md) para APIs web
- Consulte a [API Reference](api/model.md) para documentação completa 