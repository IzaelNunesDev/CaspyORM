# Definição de Modelos

Este guia explica como definir modelos no CaspyORM, incluindo campos, validação e configurações.

## Estrutura Básica

Um modelo CaspyORM é uma classe Python que herda de `Model`:

```python
from caspyorm import Model
from caspyorm.fields import Text, Integer, UUID

class User(Model):
    __table_name__ = "users"
    
    id = UUID(primary_key=True)
    name = Text(required=True)
    email = Text(index=True)
    age = Integer()
```

## Campos Disponíveis

### Campos Básicos

#### Text
Campo de texto simples.

```python
name = Text(required=True, max_length=100)
email = Text(index=True)  # Cria índice para busca eficiente
```

**Parâmetros:**
- `required`: Se o campo é obrigatório (padrão: False)
- `max_length`: Comprimento máximo do texto
- `index`: Se deve criar índice no Cassandra (padrão: False)

#### Integer
Campo numérico inteiro.

```python
age = Integer(min_value=0, max_value=150)
score = Integer(default=0)
```

**Parâmetros:**
- `min_value`: Valor mínimo permitido
- `max_value`: Valor máximo permitido
- `default`: Valor padrão

#### Float
Campo numérico de ponto flutuante.

```python
price = Float(min_value=0.0)
rating = Float(min_value=0.0, max_value=5.0)
```

#### Boolean
Campo booleano.

```python
is_active = Boolean(default=True)
verified = Boolean()
```

#### UUID
Campo UUID (identificador único universal).

```python
id = UUID(primary_key=True)
user_id = UUID()
```

### Campos de Data e Hora

#### Timestamp
Campo de data e hora.

```python
created_at = Timestamp(auto_now_add=True)
updated_at = Timestamp(auto_now=True)
```

**Parâmetros:**
- `auto_now_add`: Define automaticamente na criação
- `auto_now`: Atualiza automaticamente a cada modificação

#### Date
Campo de data.

```python
birth_date = Date()
expiry_date = Date()
```

#### Time
Campo de hora.

```python
start_time = Time()
end_time = Time()
```

### Campos Complexos

#### List
Lista de valores.

```python
tags = List(Text())
scores = List(Integer())
```

#### Set
Conjunto de valores únicos.

```python
categories = Set(Text())
user_ids = Set(UUID())
```

#### Map
Mapeamento chave-valor.

```python
metadata = Map(Text(), Text())
settings = Map(Text(), Integer())
```

## Chaves Primárias

### Chave Primária Simples

```python
class User(Model):
    __table_name__ = "users"
    
    id = UUID(primary_key=True)  # Chave de partição
    name = Text()
    email = Text()
```

### Chave Primária Composta

```python
class User(Model):
    __table_name__ = "users"
    
    tenant_id = UUID(primary_key=True)  # Primeira chave de partição
    user_id = UUID(primary_key=True)    # Segunda chave de partição
    name = Text()
    email = Text()
```

### Chave de Partição + Clustering

```python
class User(Model):
    __table_name__ = "users"
    
    tenant_id = UUID(primary_key=True)  # Chave de partição
    user_id = UUID(primary_key=True)    # Chave de clustering
    name = Text()
    email = Text()
```

## Validação

### Validação de Campos

```python
class User(Model):
    __table_name__ = "users"
    
    id = UUID(primary_key=True)
    name = Text(required=True, max_length=100)
    email = Text(required=True, max_length=255)
    age = Integer(min_value=0, max_value=150)
    score = Float(min_value=0.0, max_value=10.0)
```

### Validação Customizada

```python
from caspyorm.fields import Text
from caspyorm.exceptions import ValidationError

def validate_email(value):
    if '@' not in value:
        raise ValidationError("Email deve conter @")
    return value

class User(Model):
    __table_name__ = "users"
    
    id = UUID(primary_key=True)
    email = Text(required=True, validator=validate_email)
```

## Índices

### Índices Simples

```python
class User(Model):
    __table_name__ = "users"
    
    id = UUID(primary_key=True)
    email = Text(index=True)  # Cria índice automático
    name = Text()
```

### Índices Compostos

```python
class User(Model):
    __table_name__ = "users"
    
    id = UUID(primary_key=True)
    tenant_id = UUID(index=True)
    email = Text(index=True)
    
    # Índice composto será criado automaticamente
    # para tenant_id + email
```

## Configurações de Tabela

### Nome da Tabela

```python
class User(Model):
    __table_name__ = "users"  # Nome da tabela no Cassandra
```

### Keyspace

```python
class User(Model):
    __table_name__ = "users"
    __keyspace__ = "my_keyspace"  # Keyspace específico
```

### Configurações de Consistência

```python
class User(Model):
    __table_name__ = "users"
    __consistency_level__ = "QUORUM"  # Nível de consistência
```

## Modelos Dinâmicos

Você pode criar modelos em tempo de execução:

```python
from caspyorm import Model
from caspyorm.fields import Text, Integer, UUID

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
```

## Herança de Modelos

```python
class BaseModel(Model):
    __abstract__ = True  # Não cria tabela
    
    created_at = Timestamp(auto_now_add=True)
    updated_at = Timestamp(auto_now=True)

class User(BaseModel):
    __table_name__ = "users"
    
    id = UUID(primary_key=True)
    name = Text(required=True)
    email = Text(index=True)
```

## Exemplos Completos

### Modelo de Usuário

```python
from caspyorm import Model
from caspyorm.fields import Text, Integer, UUID, Timestamp, Boolean, List

class User(Model):
    __table_name__ = "users"
    
    # Chaves primárias
    id = UUID(primary_key=True)
    
    # Campos básicos
    name = Text(required=True, max_length=100)
    email = Text(required=True, index=True)
    age = Integer(min_value=0, max_value=150)
    
    # Campos de data
    created_at = Timestamp(auto_now_add=True)
    updated_at = Timestamp(auto_now=True)
    
    # Campos booleanos
    is_active = Boolean(default=True)
    verified = Boolean(default=False)
    
    # Campos complexos
    tags = List(Text())
    preferences = Map(Text(), Text())
```

### Modelo de Produto

```python
class Product(Model):
    __table_name__ = "products"
    
    # Chave primária composta
    category_id = UUID(primary_key=True)
    product_id = UUID(primary_key=True)
    
    # Campos básicos
    name = Text(required=True)
    description = Text()
    price = Float(min_value=0.0)
    
    # Campos com índices
    sku = Text(index=True)
    brand = Text(index=True)
    
    # Campos complexos
    images = List(Text())
    specifications = Map(Text(), Text())
    
    # Campos de data
    created_at = Timestamp(auto_now_add=True)
    updated_at = Timestamp(auto_now=True)
```

## Próximos Passos

- Veja as [Operações CRUD](../queries/crud.md) para aprender a usar os modelos
- Explore as [Operações Assíncronas](../async.md) para melhor performance
- Consulte a [API Reference](../api/model.md) para documentação completa 