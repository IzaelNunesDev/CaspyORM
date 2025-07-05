# examples/api/main_api_async.py

"""
Exemplo de API assíncrona usando FastAPI e CaspyORM com suporte assíncrono.
Este exemplo demonstra como usar a nova API async/await da CaspyORM.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from caspyorm import Model, fields, connection

# --- Modelos CaspyORM ---

class User(Model):
    __table_name__ = "users"
    
    user_id = fields.UUID(primary_key=True)
    username = fields.Text(partition_key=True)
    email = fields.Text(index=True)
    full_name = fields.Text()
    is_active = fields.Boolean(default=True)
    tags = fields.List(fields.Text())
    preferences = fields.Map(fields.Text(), fields.Text())
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
    updated_at = fields.Timestamp()

# --- Modelos Pydantic para API ---

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    tags: Optional[List[str]] = []
    preferences: Optional[dict] = {}

class UserResponse(BaseModel):
    user_id: uuid.UUID
    username: str
    email: str
    full_name: str
    is_active: bool
    tags: List[str]
    preferences: dict
    created_at: datetime

class PostCreate(BaseModel):
    title: str
    content: str
    author_id: uuid.UUID
    tags: Optional[List[str]] = []
    is_published: bool = False

class PostResponse(BaseModel):
    post_id: uuid.UUID
    title: str
    content: str
    author_id: uuid.UUID
    tags: List[str]
    likes: List[uuid.UUID]
    is_published: bool
    created_at: datetime
    updated_at: datetime

# --- Configuração FastAPI ---

app = FastAPI(
    title="CaspyORM Async API",
    description="API assíncrona usando CaspyORM com suporte async/await",
    version="1.0.0"
)

# --- Eventos de Ciclo de Vida ---

@app.on_event("startup")
async def startup_event():
    """Conecta ao Cassandra e sincroniza as tabelas na inicialização."""
    try:
        # Conectar de forma assíncrona
        await connection.connect_async(
            contact_points=['localhost'],
            port=9042,
            keyspace='caspyorm_async_demo'
        )
        
        # Sincronizar tabelas
        await User.sync_table_async(auto_apply=True)
        await Post.sync_table_async(auto_apply=True)
        
        print("✅ Conectado ao Cassandra (ASSÍNCRONO)")
        print("✅ Tabelas sincronizadas")
        
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Desconecta do Cassandra no encerramento."""
    try:
        await connection.disconnect_async()
        print("✅ Desconectado do Cassandra")
    except Exception as e:
        print(f"❌ Erro ao desconectar: {e}")

# --- Endpoints de Usuários ---

@app.post("/users/", response_model=UserResponse)
async def create_user(user_data: UserCreate):
    """Cria um novo usuário usando a API assíncrona."""
    try:
        # Usar o método async
        new_user = await User.create_async(
            user_id=uuid.uuid4(),
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            tags=user_data.tags,
            preferences=user_data.preferences,
            created_at=datetime.now()
        )
        
        return new_user.to_pydantic_model()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/", response_model=List[UserResponse])
async def list_users():
    """Lista todos os usuários usando async for."""
    try:
        # Usar async for para iterar sobre os resultados
        users = []
        async for user in User.all():
            users.append(user.to_pydantic_model())
        
        return users
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: uuid.UUID):
    """Busca um usuário específico por ID."""
    try:
        user = await User.get_async(user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        return user.to_pydantic_model()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/email/{email}", response_model=UserResponse)
async def get_user_by_email(email: str):
    """Busca um usuário por email."""
    try:
        user = await User.filter(email=email).first_async()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        return user.to_pydantic_model()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/users/{user_id}/tags")
async def update_user_tags(user_id: uuid.UUID, tags: List[str]):
    """Atualiza as tags de um usuário de forma atômica."""
    try:
        user = await User.get_async(user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Usar update_collection_async para atualização atômica
        await user.update_collection_async('tags', add=tags)
        
        return {"message": "Tags atualizadas com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/stats/count")
async def get_user_stats():
    """Retorna estatísticas de usuários usando count_async."""
    try:
        total_users = await User.all().count_async()
        active_users = await User.filter(is_active=True).count_async()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoints de Posts ---

@app.post("/posts/", response_model=PostResponse)
async def create_post(post_data: PostCreate):
    """Cria um novo post."""
    try:
        new_post = await Post.create_async(
            post_id=uuid.uuid4(),
            title=post_data.title,
            content=post_data.content,
            author_id=post_data.author_id,
            tags=post_data.tags,
            is_published=post_data.is_published,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        return new_post.to_pydantic_model()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/posts/", response_model=List[PostResponse])
async def list_posts():
    """Lista todos os posts."""
    try:
        posts = []
        async for post in Post.all():
            posts.append(post.to_pydantic_model())
        
        return posts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: uuid.UUID):
    """Busca um post específico por ID."""
    try:
        post = await Post.get_async(post_id=post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post não encontrado")
        
        return post.to_pydantic_model()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/posts/author/{author_id}", response_model=List[PostResponse])
async def get_posts_by_author(author_id: uuid.UUID):
    """Lista todos os posts de um autor específico."""
    try:
        posts = []
        async for post in Post.filter(author_id=author_id):
            posts.append(post.to_pydantic_model())
        
        return posts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/posts/{post_id}/like")
async def like_post(post_id: uuid.UUID, user_id: uuid.UUID):
    """Adiciona um like a um post de forma atômica."""
    try:
        post = await Post.get_async(post_id=post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post não encontrado")
        
        # Usar update_collection_async para adicionar like atômico
        await post.update_collection_async('likes', add={user_id})
        
        return {"message": "Post curtido com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/posts/{post_id}/like")
async def unlike_post(post_id: uuid.UUID, user_id: uuid.UUID):
    """Remove um like de um post de forma atômica."""
    try:
        post = await Post.get_async(post_id=post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post não encontrado")
        
        # Usar update_collection_async para remover like atômico
        await post.update_collection_async('likes', remove={user_id})
        
        return {"message": "Like removido com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/posts/{post_id}/tags")
async def update_post_tags(post_id: uuid.UUID, tags: List[str]):
    """Atualiza as tags de um post de forma atômica."""
    try:
        post = await Post.get_async(post_id=post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post não encontrado")
        
        # Usar update_collection_async para atualização atômica
        await post.update_collection_async('tags', add=tags)
        
        return {"message": "Tags atualizadas com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/posts/stats/count")
async def get_post_stats():
    """Retorna estatísticas de posts."""
    try:
        total_posts = await Post.all().count_async()
        published_posts = await Post.filter(is_published=True).count_async()
        
        return {
            "total_posts": total_posts,
            "published_posts": published_posts,
            "draft_posts": total_posts - published_posts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoints do Sistema ---

@app.get("/")
async def root():
    """Informações da API."""
    return {
        "message": "CaspyORM Async API",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "Async/await support",
            "FastAPI integration",
            "Atomic operations",
            "Collection updates",
            "Performance optimized"
        ]
    }

@app.get("/health")
async def health_check():
    """Verificação de saúde da API."""
    try:
        # Verificar conexão
        if not connection.is_async_connected:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        # Verificar se as tabelas existem
        user_count = await User.all().count_async()
        post_count = await Post.all().count_async()
        
        return {
            "status": "healthy",
            "database": "connected",
            "tables": {
                "users": "exists",
                "posts": "exists"
            },
            "counts": {
                "users": user_count,
                "posts": post_count
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/demo/setup")
async def setup_demo_data():
    """Configura dados de demonstração."""
    try:
        # Criar usuários de exemplo
        users = [
            await User.create_async(
                user_id=uuid.uuid4(),
                username="joao_silva",
                email="joao@example.com",
                full_name="João Silva",
                tags=["python", "developer"],
                preferences={"theme": "dark", "language": "pt-BR"},
                created_at=datetime.now()
            ),
            await User.create_async(
                user_id=uuid.uuid4(),
                username="maria_santos",
                email="maria@example.com",
                full_name="Maria Santos",
                tags=["designer", "ui/ux"],
                preferences={"theme": "light", "language": "en"},
                created_at=datetime.now()
            )
        ]
        
        # Criar posts de exemplo
        posts = [
            await Post.create_async(
                post_id=uuid.uuid4(),
                title="Introdução ao CaspyORM",
                content="CaspyORM é um ORM moderno para Cassandra...",
                author_id=users[0].user_id,
                tags=["caspyorm", "cassandra", "python"],
                is_published=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            await Post.create_async(
                post_id=uuid.uuid4(),
                title="Design de APIs Assíncronas",
                content="Como criar APIs eficientes com async/await...",
                author_id=users[1].user_id,
                tags=["api", "async", "fastapi"],
                is_published=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        return {
            "message": "Dados de demonstração criados com sucesso",
            "users_created": len(users),
            "posts_created": len(posts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 