"""
Exemplo de integração da CaspyORM com FastAPI.

Este exemplo demonstra como usar os helpers do módulo caspyorm.contrib.fastapi
para facilitar a integração entre CaspyORM e FastAPI.

Para executar este exemplo:
1. Instale as dependências: pip install caspyorm[fastapi]
2. Configure a conexão com Cassandra
3. Execute: uvicorn examples.fastapi_integration:app --reload
"""

import uuid
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel

from caspyorm import Model
from caspyorm.connection import connect
from caspyorm.fields import TextField, IntField, UUIDField, DateTimeField
from caspyorm.contrib.fastapi import (
    get_session,
    get_async_session,
    as_response_model,
    as_response_models,
    create_response_model,
    handle_caspyorm_errors
)

# Configurar conexão com Cassandra
connect(['localhost'], keyspace='test_keyspace')

# Definir modelo de usuário
class User(Model):
    __table_name__ = "users"
    id = UUIDField(primary_key=True)
    name = TextField()
    email = TextField()
    age = IntField(required=False)
    created_at = DateTimeField()

# Modelos Pydantic para requisições
class UserCreate(BaseModel):
    name: str
    email: str
    age: Optional[int] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None

# Criar modelo de resposta usando o helper
UserResponse = create_response_model(User, exclude=['created_at'])

# Inicializar FastAPI
app = FastAPI(
    title="CaspyORM + FastAPI Example",
    description="Exemplo de integração entre CaspyORM e FastAPI",
    version="1.0.0"
)

# Endpoints síncronos
@app.get("/users/sync/{user_id}", response_model=UserResponse)
def get_user_sync(user_id: str, session = Depends(get_session)):
    """Busca um usuário de forma síncrona."""
    user = User.get(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return as_response_model(user, exclude=['created_at'])

@app.post("/users/sync", response_model=UserResponse, status_code=201)
def create_user_sync(user_data: UserCreate, session = Depends(get_session)):
    """Cria um novo usuário de forma síncrona."""
    user = User.create(
        id=str(uuid.uuid4()),
        name=user_data.name,
        email=user_data.email,
        age=user_data.age
    )
    return as_response_model(user, exclude=['created_at'])

@app.get("/users/sync", response_model=List[UserResponse])
def list_users_sync(session = Depends(get_session)):
    """Lista todos os usuários de forma síncrona."""
    users = list(User.all())
    return as_response_models(users, exclude=['created_at'])

# Endpoints assíncronos
@app.get("/users/{user_id}", response_model=UserResponse)
@handle_caspyorm_errors
async def get_user(user_id: str, session = Depends(get_async_session)):
    """Busca um usuário de forma assíncrona."""
    user = await User.get_async(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return as_response_model(user, exclude=['created_at'])

@app.post("/users", response_model=UserResponse, status_code=201)
@handle_caspyorm_errors
async def create_user(user_data: UserCreate, session = Depends(get_async_session)):
    """Cria um novo usuário de forma assíncrona."""
    user = await User.create_async(
        id=str(uuid.uuid4()),
        name=user_data.name,
        email=user_data.email,
        age=user_data.age
    )
    return as_response_model(user, exclude=['created_at'])

@app.get("/users", response_model=List[UserResponse])
@handle_caspyorm_errors
async def list_users(session = Depends(get_async_session)):
    """Lista todos os usuários de forma assíncrona."""
    queryset = User.all()
    users = await queryset.all_async()
    return as_response_models(users, exclude=['created_at'])

@app.put("/users/{user_id}", response_model=UserResponse)
@handle_caspyorm_errors
async def update_user(
    user_id: str, 
    user_data: UserUpdate, 
    session = Depends(get_async_session)
):
    """Atualiza um usuário de forma assíncrona."""
    user = await User.get_async(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Atualizar apenas os campos fornecidos
    update_data = user_data.model_dump(exclude_unset=True)
    if update_data:
        await user.update_async(**update_data)
    
    return as_response_model(user, exclude=['created_at'])

@app.delete("/users/{user_id}", status_code=204)
@handle_caspyorm_errors
async def delete_user(user_id: str, session = Depends(get_async_session)):
    """Deleta um usuário de forma assíncrona."""
    user = await User.get_async(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    await user.delete_async()
    return None

# Endpoints com filtros e paginação
@app.get("/users/search/{name}", response_model=List[UserResponse])
@handle_caspyorm_errors
async def search_users_by_name(
    name: str, 
    session = Depends(get_async_session)
):
    """Busca usuários por nome."""
    queryset = User.filter(name=name)
    users = await queryset.all_async()
    return as_response_models(users, exclude=['created_at'])

@app.get("/users/count/{age}")
@handle_caspyorm_errors
async def count_users_by_age(age: int, session = Depends(get_async_session)):
    """Conta usuários por idade."""
    queryset = User.filter(age=age)
    count = await queryset.count_async()
    return {"age": age, "count": count}

# Endpoint de saúde
@app.get("/health")
async def health_check(session = Depends(get_async_session)):
    """Verifica a saúde da aplicação e conexão com banco."""
    try:
        # Tentar executar uma query simples
        count = await User.all().count_async()
        return {
            "status": "healthy",
            "database": "connected",
            "total_users": count
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}"
        )

# Middleware para logging
@app.middleware("http")
async def log_requests(request, call_next):
    """Middleware para logar requisições."""
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 