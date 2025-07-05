# CaspyORM

Um ORM moderno e Pythonic para Apache Cassandra, inspirado no Pydantic e focado em produtividade.

## Funcionalidades (Planejadas)

*   Definição de modelos intuitiva e baseada em tipos.
*   Sincronização automática de schema (`AutoSchemaSync`).
*   Consultas fluentes e encadeadas (`filter`, `get`, `all`).
*   Integração nativa com FastAPI e Pydantic para APIs web.
*   Validação de dados robusta e customizável.
*   Ferramentas de importação e exportação (JSON, CSV).

## Instalação

```bash
# Em breve
pip install caspyorm
```

## Exemplo de Uso

```python
# Em breve
from caspyorm import Model, fields

class Usuario(Model):
    id: fields.UUID(primary_key=True)
    nome: fields.Text(required=True)
    email: fields.Text(index=True)

# ...
```

## Campos de Coleção (List, Set, Map)

A CaspyORM suporta nativamente os tipos de coleção do Cassandra, permitindo modelar listas, conjuntos e mapas de forma tipada e pythonica.

### List

Use `fields.List` para armazenar listas ordenadas de valores.

```python
from caspyorm import fields, Model

class Post(Model):
    id: fields.UUID = fields.UUID(primary_key=True)
    titulo: fields.Text = fields.Text(required=True)
    tags: fields.List = fields.List(fields.Text())  # Lista de strings

# Inserindo um post com tags
post = Post.create(
    id=uuid.uuid4(),
    titulo="Exemplo com listas",
    tags=["python", "orm", "cassandra"]
)
# post.tags será uma lista Python
```

### Set

Use `fields.Set` para armazenar conjuntos de valores únicos.

```python
class Artigo(Model):
    id: fields.UUID = fields.UUID(primary_key=True)
    tags: fields.Set = fields.Set(fields.Text())  # Conjunto de strings

artigo = Artigo.create(
    id=uuid.uuid4(),
    tags={"python", "cassandra", "orm"}
)
# artigo.tags será um set Python
```

### Map

Use `fields.Map` para armazenar pares chave-valor.

```python
class Config(Model):
    id: fields.UUID = fields.UUID(primary_key=True)
    parametros: fields.Map = fields.Map(fields.Text(), fields.Text())  # Dict[str, str]

config = Config.create(
    id=uuid.uuid4(),
    parametros={"env": "prod", "debug": "false"}
)
# config.parametros será um dict Python
```

### Casos Especiais

- Ao buscar do banco, listas vazias, sets vazios e maps vazios sempre retornam `[]`, `set()` e `{}` respectivamente, mesmo que o valor no banco seja `null`.
- Ao inserir `None` para um campo de coleção, ele será convertido para o valor vazio correspondente.
- O tipo interno das coleções pode ser qualquer campo CaspyORM (ex: `fields.List(fields.Integer())`, `fields.Map(fields.Text(), fields.UUID())`).

### Dica

Você pode combinar coleções e tipos primitivos para modelar estruturas complexas, sempre respeitando as limitações do Cassandra.

---

## Exemplo Completo

```python
class Exemplo(Model):
    id: fields.UUID = fields.UUID(primary_key=True)
    lista_de_numeros: fields.List = fields.List(fields.Integer())
    conjunto_de_tags: fields.Set = fields.Set(fields.Text())
    mapa_de_config: fields.Map = fields.Map(fields.Text(), fields.Text())
```

---

## Observações

- O Cassandra não permite coleções aninhadas (ex: `list<list<text>>`), mas você pode usar tipos primitivos ou UUIDs como elementos.
- As operações de filtro e ordenação funcionam normalmente para campos de coleção, mas algumas operações avançadas (como atualização parcial de coleções) ainda não estão implementadas.

--- 