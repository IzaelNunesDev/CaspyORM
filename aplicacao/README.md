# 🚀 CaspyORM Demo API

Aplicação de demonstração completa usando **CaspyORM**, **FastAPI** e **Pydantic**.

## 📋 Funcionalidades

### 🔧 **Tecnologias Utilizadas**
- **CaspyORM**: ORM para Cassandra com funcionalidades avançadas
- **FastAPI**: Framework web moderno e rápido
- **Pydantic**: Validação de dados e serialização
- **Cassandra**: Banco de dados NoSQL distribuído

### 🎯 **Funcionalidades Demonstradas**
- ✅ **CRUD Completo**: Criar, ler, atualizar e deletar registros
- ✅ **Consultas Avançadas**: Filtros, ordenação, paginação
- ✅ **Operações em Lote**: Inserção em massa com UNLOGGED BATCH
- ✅ **Atualizações Atômicas**: Operações em coleções (listas e sets)
- ✅ **Integração Pydantic**: Validação automática de dados
- ✅ **Sincronização de Schema**: Criação automática de tabelas e índices
- ✅ **Otimizações**: `count()` e `exists()` otimizados
- ✅ **API REST**: Endpoints completos com documentação automática

## 🏗️ **Estrutura do Projeto**

```
aplicacao/
├── app/
│   └── main.py              # Aplicação principal FastAPI
├── config/
│   └── database.py          # Configuração do banco de dados
├── models/
│   ├── user.py              # Modelo de usuário
│   └── post.py              # Modelo de post
├── routers/
│   ├── users.py             # Endpoints de usuários
│   └── posts.py             # Endpoints de posts
├── requirements.txt         # Dependências
├── run.py                   # Script de inicialização
└── README.md               # Este arquivo
```

## 🚀 **Como Executar**

### **Pré-requisitos**
1. **Cassandra** rodando em `localhost:9042`
2. **Python 3.8+** instalado
3. **CaspyORM** instalado localmente

### **Passo 1: Instalar Dependências**
```bash
cd aplicacao
pip install -r requirements.txt
```

### **Passo 2: Executar a Aplicação**
```bash
python run.py
```

### **Passo 3: Acessar a API**
- 🌐 **API**: http://localhost:8000
- 📖 **Documentação**: http://localhost:8000/docs
- 🔍 **ReDoc**: http://localhost:8000/redoc
- 🏥 **Health Check**: http://localhost:8000/health
- 📊 **Setup Demo**: http://localhost:8000/demo/setup

## 📊 **Modelos de Dados**

### **User (Usuário)**
```python
{
    "id": "uuid",
    "username": "string",
    "email": "string (indexado)",
    "full_name": "string",
    "is_active": "boolean",
    "tags": ["string"],
    "preferences": {"key": "value"},
    "created_at": "timestamp"
}
```

### **Post (Post)**
```python
{
    "id": "uuid",
    "title": "string",
    "content": "string",
    "author_id": "uuid (indexado)",
    "tags": ["string"],
    "likes": {"uuid"},
    "is_published": "boolean",
    "created_at": "timestamp",
    "updated_at": "timestamp"
}
```

## 🔗 **Endpoints da API**

### **Usuários (`/users`)**
- `POST /users/` - Criar usuário
- `GET /users/` - Listar usuários (com paginação)
- `GET /users/{user_id}` - Buscar usuário por ID
- `GET /users/email/{email}` - Buscar usuário por email
- `PUT /users/{user_id}/tags` - Atualizar tags do usuário
- `GET /users/stats/count` - Estatísticas de usuários

### **Posts (`/posts`)**
- `POST /posts/` - Criar post
- `GET /posts/` - Listar posts (com paginação)
- `GET /posts/{post_id}` - Buscar post por ID
- `GET /posts/author/{author_id}` - Posts por autor
- `POST /posts/{post_id}/like` - Curtir post
- `DELETE /posts/{post_id}/like` - Descurtir post
- `PUT /posts/{post_id}/tags` - Atualizar tags do post
- `GET /posts/stats/count` - Estatísticas de posts

### **Sistema (`/`)**
- `GET /` - Informações da API
- `GET /health` - Verificação de saúde
- `GET /demo/setup` - Configurar dados de demonstração

## 🎯 **Funcionalidades Demonstradas**

### **1. CRUD Básico**
```python
# Criar usuário
user = User.create_user("joao", "joao@example.com", "João Silva")

# Buscar usuário
user = User.get(id=user_id)

# Atualizar usuário
user.update(is_active=False)

# Deletar usuário
user.delete()
```

### **2. Consultas Avançadas**
```python
# Filtros
users = User.filter(is_active=True).all()

# Paginação
users, next_page = User.all().page(page_size=10)

# Contagem otimizada
count = User.filter(is_active=True).count()

# Verificar existência
exists = User.filter(email="test@example.com").exists()
```

### **3. Operações em Lote**
```python
# Inserção em massa
users_data = [
    {"username": "user1", "email": "user1@example.com"},
    {"username": "user2", "email": "user2@example.com"}
]
User.bulk_create(users_data)
```

### **4. Atualizações Atômicas**
```python
# Adicionar tags de forma atômica
user.update_collection('tags', add=['python', 'cassandra'])

# Adicionar like de forma atômica
post.add_like(user_id)

# Remover like de forma atômica
post.remove_like(user_id)
```

### **5. Integração Pydantic**
```python
# Modelo Pydantic gerado automaticamente
UserPydantic = User.as_pydantic("UserCreate")
UserResponse = User.as_pydantic("UserResponse")

# Validação automática na API
@router.post("/", response_model=UserResponse)
async def create_user(user_data: UserPydantic):
    user = User.create(**user_data.dict())
    return user.to_pydantic_model()
```

## 🔧 **Configuração do Cassandra**

### **Criar Keyspace**
```sql
CREATE KEYSPACE caspyorm_demo 
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};
```

### **Configuração Automática**
A aplicação cria automaticamente:
- ✅ Keyspace `caspyorm_demo`
- ✅ Tabelas `users` e `posts`
- ✅ Índices secundários para campos indexados
- ✅ Dados de demonstração

## 📈 **Performance e Otimizações**

### **Consultas Otimizadas**
- `count()` usa `SELECT COUNT(*)` nativo
- `exists()` usa `SELECT <pk> LIMIT 1`
- Paginação com `page()` para grandes datasets
- Operações em lote com UNLOGGED BATCH

### **Índices Automáticos**
- Campos marcados com `index=True` criam índices secundários
- Consultas por email e author_id são otimizadas

### **Operações Atômicas**
- Atualizações de coleções são atômicas
- Likes e tags são atualizados sem race conditions

## 🧪 **Testando a API**

### **1. Configurar Dados de Demo**
```bash
curl http://localhost:8000/demo/setup
```

### **2. Criar Usuário**
```bash
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Usuário Teste"
  }'
```

### **3. Listar Usuários**
```bash
curl http://localhost:8000/users/
```

### **4. Criar Post**
```bash
curl -X POST "http://localhost:8000/posts/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Meu Post",
    "content": "Conteúdo do post",
    "author_id": "USER_ID_AQUI",
    "tags": ["teste", "demo"]
  }'
```

### **5. Curtir Post**
```bash
curl -X POST "http://localhost:8000/posts/POST_ID/like?user_id=USER_ID"
```

## 🎉 **Próximos Passos**

1. **Adicionar Autenticação**: JWT tokens
2. **Implementar Cache**: Redis para consultas frequentes
3. **Adicionar Logs**: Estruturados com loguru
4. **Métricas**: Prometheus para monitoramento
5. **Testes**: Testes automatizados com pytest
6. **Docker**: Containerização da aplicação
7. **CI/CD**: Pipeline de deploy automático

## 📝 **Contribuição**

Esta aplicação demonstra as capacidades completas da **CaspyORM** em um cenário real. Use como referência para implementar suas próprias aplicações!

---

**Desenvolvido com ❤️ usando CaspyORM, FastAPI e Pydantic** 