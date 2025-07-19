# Operações CRUD

Este guia explica como realizar operações CRUD (Create, Read, Update, Delete) no CaspyORM.

## Criar (Create)

### Criar um Registro

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

# Criar usuário
user = User.create(
    id=uuid.uuid4(),
    name="João Silva",
    email="joao@example.com",
    age=30
)
```

### Criar Múltiplos Registros

```python
# Criar múltiplos usuários
users_data = [
    {"id": uuid.uuid4(), "name": "User 1", "email": "user1@example.com", "age": 25},
    {"id": uuid.uuid4(), "name": "User 2", "email": "user2@example.com", "age": 30},
    {"id": uuid.uuid4(), "name": "User 3", "email": "user3@example.com", "age": 35},
]

users = User.bulk_create([User(**data) for data in users_data])
```

### Criar com Validação

```python
# O modelo validará automaticamente os dados
try:
    user = User.create(
        id=uuid.uuid4(),
        name="",  # Campo obrigatório vazio
        email="invalid-email",  # Email inválido
        age=200  # Idade fora do range
    )
except ValidationError as e:
    print(f"Erro de validação: {e}")
```

## Ler (Read)

### Buscar por Chave Primária

```python
# Buscar por ID
user = User.get(id=user_id)

# Buscar por múltiplas chaves primárias
class Product(Model):
    __table_name__ = "products"
    
    category_id = UUID(primary_key=True)
    product_id = UUID(primary_key=True)
    name = Text()

product = Product.get(category_id=cat_id, product_id=prod_id)
```

### Buscar por Campos Indexados

```python
# Buscar por email (campo indexado)
user = User.get(email="joao@example.com")

# Buscar por múltiplos campos
user = User.get(email="joao@example.com", age=30)
```

### Buscar Múltiplos Registros

```python
# Buscar todos os usuários
all_users = User.all()

# Buscar com filtros
young_users = User.filter(age__lt=30).all()
active_users = User.filter(is_active=True).all()

# Buscar com limite
recent_users = User.filter().limit(10).all()
```

### Filtros Avançados

```python
# Filtros de comparação
users = User.filter(age__gte=25).all()  # Maior ou igual
users = User.filter(age__lte=50).all()  # Menor ou igual
users = User.filter(age__gt=20).all()   # Maior que
users = User.filter(age__lt=40).all()   # Menor que

# Filtros de texto
users = User.filter(name__contains="João").all()
users = User.filter(name__startswith="Jo").all()
users = User.filter(name__endswith="Silva").all()

# Filtros múltiplos
users = User.filter(age__gte=25, is_active=True).all()

# Filtros com OR (usando Q objects)
from caspyorm import Q

users = User.filter(Q(age__lt=25) | Q(age__gt=50)).all()
users = User.filter(Q(name__contains="João") & Q(is_active=True)).all()
```

### Ordenação

```python
# Ordenar por campo
users = User.filter().order_by("name").all()
users = User.filter().order_by("-age").all()  # Ordem decrescente

# Ordenar por múltiplos campos
users = User.filter().order_by("age", "name").all()
```

### Paginação

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

### Contagem e Existência

```python
# Contar registros
count = User.filter(age__gte=25).count()
total_users = User.count()

# Verificar existência
exists = User.filter(email="joao@example.com").exists()
```

## Atualizar (Update)

### Atualizar um Registro

```python
# Buscar e atualizar
user = User.get(id=user_id)
user.update(name="João Silva Santos", age=31)

# Ou atualizar diretamente
user.name = "João Silva Santos"
user.age = 31
user.save()
```

### Atualizar Múltiplos Registros

```python
# Atualizar todos os usuários ativos
users = User.filter(is_active=True).all()
for user in users:
    user.update(last_login=datetime.now())
```

### Atualizar Campos Específicos

```python
# Atualizar apenas alguns campos
user.update_fields(["name", "age"], name="Novo Nome", age=32)
```

### Atualizar com Validação

```python
try:
    user.update(age=200)  # Idade inválida
except ValidationError as e:
    print(f"Erro de validação: {e}")
```

## Deletar (Delete)

### Deletar um Registro

```python
# Deletar por instância
user = User.get(id=user_id)
user.delete()

# Deletar por chave primária
User.delete(id=user_id)
```

### Deletar Múltiplos Registros

```python
# Deletar todos os usuários inativos
User.filter(is_active=False).delete()

# Deletar usuários por idade
User.filter(age__lt=18).delete()
```

### Deletar com Filtros Complexos

```python
# Deletar usuários que não fizeram login há muito tempo
from datetime import datetime, timedelta

cutoff_date = datetime.now() - timedelta(days=365)
User.filter(last_login__lt=cutoff_date, is_active=False).delete()
```

## Operações Assíncronas

Todas as operações CRUD têm versões assíncronas:

```python
import asyncio

async def main():
    # Criar
    user = await User.create_async(
        id=uuid.uuid4(),
        name="Maria Santos",
        email="maria@example.com",
        age=28
    )
    
    # Buscar
    found_user = await User.get_async(email="maria@example.com")
    
    # Atualizar
    await user.update_async(age=29)
    
    # Deletar
    await user.delete_async()
    
    # Operações em lote
    users = await User.bulk_create_async([...])
    
    # Queries complexas
    users = await User.filter(age__gte=25).all_async()
    count = await User.filter(is_active=True).count_async()

# Executar
asyncio.run(main())
```

## Transações

### Transações Simples

```python
from caspyorm import transaction

with transaction():
    user = User.create(name="João", email="joao@example.com")
    user.update(age=30)
    # Se algo falhar, tudo é revertido
```

### Transações Assíncronas

```python
async with transaction_async():
    user = await User.create_async(name="João", email="joao@example.com")
    await user.update_async(age=30)
```

## Exemplos Práticos

### Sistema de Blog

```python
class Post(Model):
    __table_name__ = "posts"
    
    id = UUID(primary_key=True)
    author_id = UUID(index=True)
    title = Text(required=True)
    content = Text()
    published = Boolean(default=False)
    created_at = Timestamp(auto_now_add=True)
    updated_at = Timestamp(auto_now=True)

# Criar post
post = Post.create(
    id=uuid.uuid4(),
    author_id=user.id,
    title="Meu Primeiro Post",
    content="Conteúdo do post...",
    published=True
)

# Buscar posts de um autor
author_posts = Post.filter(author_id=user.id).order_by("-created_at").all()

# Buscar posts publicados
published_posts = Post.filter(published=True).order_by("-created_at").all()

# Atualizar post
post.update(title="Título Atualizado", content="Novo conteúdo...")

# Deletar post
post.delete()
```

### Sistema de E-commerce

```python
class Order(Model):
    __table_name__ = "orders"
    
    id = UUID(primary_key=True)
    customer_id = UUID(index=True)
    status = Text(index=True)  # pending, paid, shipped, delivered
    total = Float()
    created_at = Timestamp(auto_now_add=True)

# Criar pedido
order = Order.create(
    id=uuid.uuid4(),
    customer_id=customer.id,
    status="pending",
    total=99.99
)

# Buscar pedidos pendentes
pending_orders = Order.filter(status="pending").all()

# Atualizar status
order.update(status="paid")

# Buscar pedidos de um cliente
customer_orders = Order.filter(customer_id=customer.id).order_by("-created_at").all()
```

## Próximos Passos

- Veja as [Operações Assíncronas](../async.md) para melhor performance
- Explore a [Integração com FastAPI](../fastapi.md) para APIs web
- Consulte a [API Reference](../api/model.md) para documentação completa 