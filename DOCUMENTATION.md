# Documentação Oficial do CaspyORM

**CaspyORM** é um Object-Relational Mapper (ORM) moderno, assíncrono e de alta performance para o Apache Cassandra, construído com Python. Ele foi projetado para ser intuitivo, poderoso e fácil de integrar com frameworks web modernos como FastAPI.

A filosofia do CaspyORM é fornecer uma API expressiva e familiar (inspirada no Django ORM) que abstrai a complexidade do CQL (Cassandra Query Language), ao mesmo tempo que expõe os recursos poderosos do Cassandra, como operações em lote, atualizações atômicas e paginação eficiente.

## Principais Recursos

- **API Síncrona e Assíncrona:** Use `async/await` para aplicações de alta performance ou a API síncrona tradicional para scripts e tarefas mais simples.
- **Sintaxe de Query Expressiva:** Construa consultas complexas de forma encadeada e legível com o `QuerySet` (`filter`, `order_by`, `limit`, etc.).
- **Validação de Dados:** Tipos de campo robustos que validam e convertem dados automaticamente.
- **Sincronização de Schema:** Crie e atualize tabelas no Cassandra automaticamente a partir da definição dos seus modelos com o método `sync_table()`.
- **Integração com Pydantic/FastAPI:** Gere modelos Pydantic a partir dos seus modelos CaspyORM com um único comando (`as_pydantic()`), simplificando a criação de APIs.
- **Recursos Avançados do Cassandra:** Suporte para operações em lote (`bulk_create`), atualizações atômicas (`update_collection`) e paginação eficiente (`page()`).
- **Sistema de Logging e Avisos:** Logs detalhados para depuração e avisos inteligentes para ajudar a evitar queries ineficientes.

---

*Esta documentação será expandida nas próximas etapas.*

## Instalação

Para instalar o CaspyORM, use o pip:

```bash
pip install caspyorm
```

## Conectando ao Cassandra

A conexão é o primeiro passo para interagir com o banco de dados. O CaspyORM oferece uma API simples para gerenciar conexões síncronas e assíncronas.

### Conexão Síncrona

Use a função `connection.connect()` para estabelecer uma conexão síncrona. Ela gerencia um pool de conexões global que será usado por todas as operações de banco de dados.

```python
from caspyorm import connection

# Lista de nós do cluster Cassandra
CASSANDRA_HOSTS = ['127.0.0.1']
KEYSPACE = 'meu_app_db'

# Conectar ao Cassandra
connection.connect(contact_points=CASSANDRA_HOSTS, keyspace=KEYSPACE)

print("Conexão estabelecida com sucesso!")

# ... seu código aqui ...

# É uma boa prática desconectar ao final da aplicação
connection.disconnect()
```

**Parâmetros de `connect()`:**

- `contact_points` (obrigatório): Uma lista de endereços IP dos nós do seu cluster Cassandra.
- `keyspace` (obrigatório): O nome do keyspace que sua aplicação usará. Se não existir, o CaspyORM tentará criá-lo automaticamente.
- `port` (opcional): A porta do Cassandra (padrão: `9042`).
- `username` e `password` (opcional): Se o seu cluster exigir autenticação.

### Conexão Assíncrona

Para aplicações assíncronas (como em um servidor FastAPI), use `connection.connect_async()`.

```python
import asyncio
from caspyorm import connection

CASSANDRA_HOSTS = ['127.0.0.1']
KEYSPACE = 'meu_app_db'

async def main():
    # Conectar de forma assíncrona
    await connection.connect_async(contact_points=CASSANDRA_HOSTS, keyspace=KEYSPACE)
    
    print("Conexão assíncrona estabelecida com sucesso!")
    
    # ... seu código assíncrono aqui ...
    
    await connection.disconnect_async()

# Executar a aplicação
asyncio.run(main())
```

## Definindo Modelos

Os modelos são o coração da sua aplicação. Cada modelo é uma classe Python que herda de `caspyorm.Model` e representa uma tabela no Cassandra.

### Estrutura Básica

Para criar um modelo, defina uma classe com atributos que são instâncias dos campos do `caspyorm.fields`.

```python
from caspyorm import Model, fields
import uuid
from datetime import datetime

class Usuario(Model):
    # O nome da tabela no Cassandra
    __table_name__ = 'usuarios'

    # Definição dos campos (colunas)
    id = fields.UUID(primary_key=True, default=uuid.uuid4)
    nome = fields.Text(required=True)
    email = fields.Text(index=True)
    idade = fields.Integer()
    ativo = fields.Boolean(default=True)
    data_criacao = fields.Timestamp(default=datetime.utcnow)
```

- `__table_name__`: (Obrigatório) Define o nome da tabela no banco de dados.
- `Atributos de Classe`: Cada atributo definido com um `fields.*` corresponde a uma coluna na tabela.

### Sincronizando o Schema

Depois de definir seu modelo, você pode criar a tabela correspondente no Cassandra usando o método `sync_table()`:

```python
# Isso irá criar a tabela 'usuarios' se ela não existir
# ou adicionar/alterar colunas se o modelo for modificado.
Usuario.sync_table()
```

### Tipos de Campos (`fields`)

O CaspyORM oferece um conjunto rico de tipos de campo que mapeiam diretamente para os tipos de dados do Cassandra.

#### Campos Primitivos

- `fields.UUID`: Para identificadores únicos universais. Se usado como `primary_key`, pode gerar um `uuid.uuid4` por padrão.
- `fields.Text`: Para strings de texto (`text`).
- `fields.Integer`: Para números inteiros (`int`).
- `fields.Float`: Para números de ponto flutuante (`float`).
- `fields.Boolean`: Para valores verdadeiros/falsos (`boolean`).
- `fields.Timestamp`: Para data e hora (`timestamp`). Mapeia para objetos `datetime` em Python.

#### Campos de Coleção

- `fields.List(inner_field)`: Para listas de valores. Ex: `fields.List(fields.Text())`.
- `fields.Set(inner_field)`: Para conjuntos de valores únicos. Ex: `fields.Set(fields.Integer())`.
- `fields.Map(key_field, value_field)`: Para mapas (dicionários) chave-valor. Ex: `fields.Map(fields.Text(), fields.Text())`.

### Opções dos Campos

Você pode configurar o comportamento de cada campo com os seguintes parâmetros:

- `primary_key=True`: Marca o campo como a chave primária da tabela. Uma chave primária simples também atua como a chave de partição.
- `partition_key=True`: Essencial para o Cassandra. Marca o campo (ou campos, em uma chave composta) como a chave de partição. Todas as queries devem, preferencialmente, filtrar por este campo.
- `clustering_key=True`: Usado em chaves primárias compostas para ordenar os dados dentro de uma partição.
- `index=True`: Cria um índice secundário no campo. Útil para campos que são frequentemente filtrados, mas não fazem parte da chave primária. Use com moderação.
- `required=True`: Torna o campo obrigatório. Uma exceção `ValidationError` será levantada se o campo não for fornecido ao criar uma instância.
- `default`: Fornece um valor padrão para o campo se nenhum for especificado. Pode ser um valor ou uma função (como `default=datetime.utcnow`).

## Operações CRUD (Criar, Ler, Atualizar, Deletar)

O CaspyORM fornece uma API intuitiva para as operações básicas de banco de dados.

### Criar Registros

Você pode criar novos registros de duas maneiras: usando o método de classe `create()` ou instanciando um objeto e chamando `save()`.

**Usando `create()` (síncrono):**

```python
# Cria e salva um novo usuário no banco de dados em um único passo
novo_usuario = Usuario.create(
    nome="João Silva", 
    email="joao.silva@example.com", 
    idade=30
)
print(f"Usuário criado com ID: {novo_usuario.id}")
```

**Usando `save()` (síncrono):**

```python
# Instancia o objeto primeiro
usuario_para_salvar = Usuario(nome="Maria Santos", email="maria.santos@example.com", idade=25)
# Salva no banco de dados
usuario_para_salvar.save()
print(f"Usuário salvo com ID: {usuario_para_salvar.id}")
```

**Versões Assíncronas:**

```python
# Com create_async
novo_usuario_async = await Usuario.create_async(nome="Ana Costa", email="ana.costa@example.com")

# Com save_async
usuario_para_salvar_async = Usuario(nome="Pedro Lima", email="pedro.lima@example.com")
await usuario_para_salvar_async.save_async()
```

### Ler Registros

Para ler dados, você pode buscar um único registro por sua chave primária ou filtrar múltiplos registros.

**Buscando um único registro com `get()`:**

```python
# Busca um usuário pelo seu ID (chave primária)
usuario_encontrado = Usuario.get(id=novo_usuario.id)
print(f"Usuário encontrado: {usuario_encontrado.nome}")

# Versão assíncrona
usuario_encontrado_async = await Usuario.get_async(id=novo_usuario.id)
```

**Buscando múltiplos registros com `filter()`:**

O método `filter()` retorna um `QuerySet`, que é uma representação preguiçosa (lazy) da sua consulta. A consulta só é executada quando você tenta acessar os dados.

```python
# Encontra todos os usuários com o email especificado (campo indexado)
usuarios_com_email = Usuario.filter(email="joao.silva@example.com").all()

for usuario in usuarios_com_email:
    print(f"- {usuario.nome}")

# Versão assíncrona
usuarios_async = await Usuario.filter(email="joao.silva@example.com").all_async()
```

### Atualizar Registros

Você pode atualizar um registro de duas formas: `save()` para uma atualização completa ou `update()` para uma atualização parcial e otimizada.

**Atualização completa com `save()`:**

O método `save()` sobrescreve o registro inteiro. Você deve carregar o objeto, modificar seus atributos e então salvá-lo.

```python
usuario_para_atualizar = Usuario.get(id=novo_usuario.id)
usuario_para_atualizar.idade = 31
usuario_para_atualizar.save() # Salva o objeto inteiro
```

**Atualização parcial com `update()` (Recomendado):**

O método `update()` é mais eficiente, pois atualiza apenas os campos que você especificar, gerando uma query `UPDATE` mais enxuta.

```python
usuario_para_atualizar = Usuario.get(id=novo_usuario.id)
usuario_para_atualizar.update(idade=32, ativo=False)

print(f"Idade atualizada para: {usuario_para_atualizar.idade}")

# Versão assíncrona
await usuario_para_atualizar.update_async(idade=33)
```

### Deletar Registros

Para deletar um registro, carregue a instância e chame o método `delete()`.

```python
usuario_para_deletar = Usuario.get(id=novo_usuario.id)
usuario_para_deletar.delete()
print("Usuário deletado com sucesso.")

# Versão assíncrona
usuario_para_deletar_async = await Usuario.get_async(id=outro_usuario.id)
await usuario_para_deletar_async.delete_async()
```

## Consultas com QuerySet

O `QuerySet` é uma das ferramentas mais poderosas do CaspyORM. Ele permite construir consultas complexas de forma preguiçosa (lazy) e encadeada. A consulta ao banco de dados só é executada quando você avalia o `QuerySet` (por exemplo, chamando `.all()`, `list()`, ou iterando sobre ele).

### Filtrando Dados (`filter`)

O método `filter()` é a base para todas as consultas. Você pode encadear múltiplos filtros.

```python
# Filtro simples
usuarios_ativos = Usuario.filter(ativo=True)

# Filtro encadeado
usuarios_ativos_com_idade = Usuario.filter(ativo=True).filter(idade=30)
```

#### Operadores de Consulta

Para filtros mais complexos, você pode usar operadores especiais no nome do campo, separados por `__` (duplo underscore):

- `__gt`: Maior que (`>`)
- `__gte`: Maior ou igual a (`>=`)
- `__lt`: Menor que (`<`)
- `__lte`: Menor ou igual a (`<=`)
- `__in`: Corresponde a qualquer valor em uma lista (`IN`)

```python
# Usuários com mais de 25 anos
usuarios_maiores_de_25 = Usuario.filter(idade__gt=25).all()

# Usuários cujos nomes estão em uma lista
usuarios_especificos = Usuario.filter(nome__in=["João Silva", "Maria Santos"]).all()
```

### Ordenando Resultados (`order_by`)

Use `order_by()` para especificar a ordem dos resultados. A ordenação no Cassandra depende da sua `clustering_key`.

```python
# Ordena por data de criação, do mais recente para o mais antigo
usuarios_recentes = Usuario.order_by("-data_criacao").all()

# Ordena pelo nome (requer que 'nome' seja uma clustering key)
usuarios_por_nome = Usuario.order_by("nome").all()
```

### Limitando Resultados (`limit`)

Para restringir o número de registros retornados, use `limit()`.

```python
# Pega os 5 primeiros usuários
primeiros_5_usuarios = Usuario.filter(ativo=True).limit(5)
```

### Contando e Verificando Existência

- `count()`: Retorna o número de registros que correspondem à consulta. É uma operação otimizada que não carrega os dados.
- `exists()`: Retorna `True` se pelo menos um registro corresponder à consulta, e `False` caso contrário. Também é otimizado.

```python
# Conta quantos usuários ativos existem
total_ativos = Usuario.filter(ativo=True).count()

# Verifica se existe algum usuário com um email específico
tem_usuario = Usuario.filter(email="email.inexistente@example.com").exists()
```

### `allow_filtering()` e Boas Práticas

O Cassandra exige que as consultas sejam muito eficientes. Por padrão, ele só permite filtros em campos que fazem parte da chave primária ou que possuem um índice. Se você tentar filtrar por um campo não indexado, o CaspyORM (e o Cassandra) levantará um erro.

Para contornar isso, você pode usar `allow_filtering()`, mas **use com cuidado**, pois pode levar a queries lentas.

```python
# Supondo que 'idade' não é indexado
# A linha abaixo irá falhar por padrão
# usuarios = Usuario.filter(idade=40).all()

# Com allow_filtering(), a query é permitida
# O CaspyORM também emitirá um aviso para alertá-lo sobre a possível ineficiência
usuarios = Usuario.filter(idade=40).allow_filtering().all()
```

### Paginação com `page()`

Para lidar com grandes volumes de dados, use o método `page()` para buscar resultados em lotes (páginas). Ele retorna os resultados da página atual e um `paging_state` que você usa para solicitar a próxima página.

```python
page_size = 100
queryset = Usuario.filter(ativo=True)
paging_state = None

while True:
    resultados, paging_state = queryset.page(page_size=page_size, paging_state=paging_state)
    
    for usuario in resultados:
        print(usuario.nome)
    
    if not paging_state:
        break # Não há mais páginas
```

## Operações Avançadas

O CaspyORM também oferece suporte a operações mais avançadas para otimizar a performance e lidar com casos de uso complexos.

### Criação em Lote (`bulk_create`)

Para inserir um grande número de registros de uma só vez, usar `create()` em um loop pode ser ineficiente. O método `bulk_create()` envia todos os registros em um único lote (batch) para o Cassandra, reduzindo drasticamente a latência de rede.

```python
from caspyorm.models import Batch

# Crie uma lista de instâncias do seu modelo (sem salvá-las)
usuarios_para_criar = [
    Usuario(nome="Carlos Mendes", email="carlos@example.com"),
    Usuario(nome="Beatriz Costa", email="beatriz@example.com"),
    Usuario(nome="Daniel Almeida", email="daniel@example.com")
]

# Use o contexto Batch para executar a operação
with Batch() as b:
    Usuario.bulk_create(usuarios_para_criar, batch=b)

print(f"{len(usuarios_para_criar)} usuários criados em lote.")

# Versão assíncrona
async with Batch(is_async=True) as b:
    await Usuario.bulk_create_async(usuarios_para_criar, batch=b)
```

### Atualizações Atômicas de Coleções

O Cassandra permite adicionar ou remover elementos de uma coleção (list, set, map) de forma atômica, sem precisar ler e reescrever a coleção inteira. O CaspyORM expõe essa funcionalidade através do método `update_collection()`.

Isso é extremamente útil para evitar condições de corrida quando múltiplos clientes tentam modificar a mesma coleção ao mesmo tempo.

```python
# Suponha um modelo de Post com um campo de tags
class Post(Model):
    __table_name__ = 'posts'
    id = fields.UUID(primary_key=True)
    titulo = fields.Text()
    tags = fields.List(fields.Text()) # Uma lista de tags

# ...

post = Post.get(id=post_id)

# Adicionar uma tag à lista (operação atômica de append)
post.update_collection("tags", ["nova-tag"], operation="add")

# Remover uma tag da lista (operação atômica de remove)
post.update_collection("tags", ["tag-antiga"], operation="remove")

# Versão assíncrona
await post.update_collection_async("tags", ["outra-nova-tag"], operation="add")
```

- `operation="add"`: Adiciona os itens à coleção. Para um `Map`, você passaria um dicionário.
- `operation="remove"`: Remove os itens da coleção.

## Integração com FastAPI e Pydantic

Uma das funcionalidades mais poderosas do CaspyORM é sua integração nativa com Pydantic, o que o torna perfeito para uso com FastAPI.

### Gerando Modelos Pydantic

Qualquer modelo do CaspyORM pode ser convertido em um modelo Pydantic com o método de classe `as_pydantic()`. Isso cria uma classe Pydantic que pode ser usada para validação de dados em rotas de API, tanto para requests quanto para responses.

```python
# Relembrando nosso modelo Usuario
class Usuario(Model):
    __table_name__ = 'usuarios'
    id = fields.UUID(primary_key=True, default=uuid.uuid4)
    nome = fields.Text(required=True)
    email = fields.Text(index=True)
    # ... outros campos

# Gerar o modelo Pydantic
PydanticUsuario = Usuario.as_pydantic()

# Você também pode gerar um modelo para criação (sem o ID, por exemplo)
PydanticUsuarioCreate = Usuario.as_pydantic(exclude=["id"])
```

### Exemplo Completo com FastAPI

Abaixo está um exemplo de uma API simples para um CRUD de usuários, mostrando como a integração funciona na prática.

```python
# main.py
from fastapi import FastAPI, HTTPException
from typing import List
import uvicorn

from caspyorm import connection
from .models import Usuario # Supondo que seu modelo está em models.py

# --- Configuração da Aplicação ---
app = FastAPI(
    title="API de Usuários com CaspyORM",
    description="Um exemplo de CRUD usando FastAPI e CaspyORM."
)

# Gerar modelos Pydantic a partir do modelo CaspyORM
PydanticUsuario = Usuario.as_pydantic()
PydanticUsuarioCreate = Usuario.as_pydantic(exclude=["id", "data_criacao"])

# --- Eventos de Ciclo de Vida da Aplicação ---
@app.on_event("startup")
async def startup_event():
    """Conecta ao banco de dados e sincroniza a tabela na inicialização."""
    await connection.connect_async(contact_points=['127.0.0.1'], keyspace='fastapi_db')
    await Usuario.sync_table_async()

@app.on_event("shutdown")
async def shutdown_event():
    """Desconecta do banco de dados no encerramento."""
    await connection.disconnect_async()

# --- Rotas da API ---
@app.post("/usuarios/", response_model=PydanticUsuario, status_code=201)
async def criar_usuario(usuario_data: PydanticUsuarioCreate):
    """Cria um novo usuário.

    O corpo do request é validado pelo PydanticUsuarioCreate.
    """
    novo_usuario = await Usuario.create_async(**usuario_data.dict())
    return novo_usuario

@app.get("/usuarios/", response_model=List[PydanticUsuario])
async def listar_usuarios():
    """Lista todos os usuários.

    A resposta é uma lista de objetos validados pelo PydanticUsuario.
    """
    usuarios = await Usuario.all_async()
    return usuarios

@app.get("/usuarios/{usuario_id}", response_model=PydanticUsuario)
async def obter_usuario(usuario_id: uuid.UUID):
    """Busca um usuário pelo seu ID."""
    try:
        usuario = await Usuario.get_async(id=usuario_id)
        return usuario
    except Usuario.DoesNotExist:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

# --- Executar a Aplicação ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

```
```
```
```
