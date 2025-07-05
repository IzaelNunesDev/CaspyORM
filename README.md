# CaspyORM

Um ORM moderno e Pythonic para Apache Cassandra, inspirado no Pydantic e focado em produtividade e performance.

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
    parametros = fields.Map(fields.Text(), fields.Text())  # Dict[str, str]

config = Config.create(
    id=uuid.uuid4(),
    parametros={"env": "prod", "debug": "false"}
)
```

## 🔗 Integração Pydantic

```python
# Gerar modelo Pydantic a partir do modelo CaspyORM
PydanticUsuario = Usuario.as_pydantic()

# Converter instância CaspyORM para Pydantic
pydantic_usuario = usuario.to_pydantic_model()

# Usar com FastAPI
from fastapi import FastAPI

app = FastAPI()

@app.post("/usuarios/")
async def criar_usuario(usuario: PydanticUsuario):
    return Usuario.create(**usuario.dict())
```

## 📈 Performance Tips

1. **Use índices** para campos frequentemente filtrados
2. **Bulk operations** para inserções em massa
3. **Count/Exists** em vez de `len(all())` ou `first()`
4. **Paginação** para grandes datasets
5. **Update atômico** para coleções em vez de recarregar objetos

## 🛠️ Configuração

```python
from caspyorm import connection

# Configuração básica
connection.setup(
    contact_points=['localhost'],
    keyspace='meu_keyspace'
)

# Configuração avançada
connection.setup(
    contact_points=['cassandra1', 'cassandra2'],
    keyspace='meu_keyspace',
    username='user',
    password='pass',
    protocol_version=4
)
```

## 🧪 Testes

A CaspyORM possui uma suíte completa de testes (86 testes) cobrindo:

- Definição de modelos e validação
- Operações CRUD básicas e avançadas
- Coleções (List, Set, Map)
- Consultas e filtros
- Sincronização de schema
- Integração Pydantic
- Tratamento de exceções
- Performance e otimizações

```bash
# Executar todos os testes
python -m pytest tests/

# Executar testes específicos
python -m pytest tests/test_11_nivel3_improvements.py -v
```

## 📝 Licença

MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor, leia as diretrizes de contribuição antes de submeter pull requests.

---

**CaspyORM** - ORM moderno e performático para Apache Cassandra 🚀 