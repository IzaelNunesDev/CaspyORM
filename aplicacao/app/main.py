"""
Aplicação principal FastAPI usando CaspyORM.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Adicionar o diretório pai ao path para importar a biblioteca
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from aplicacao.config.database import setup_database, create_keyspace
from aplicacao.routers import users, posts

# Criar aplicação FastAPI
app = FastAPI(
    title="CaspyORM Demo API",
    description="API de demonstração usando CaspyORM, FastAPI e Pydantic",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(users.router)
app.include_router(posts.router)

@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização da aplicação."""
    print("🚀 Iniciando aplicação CaspyORM Demo...")
    
    # Criar keyspace
    if not create_keyspace():
        print("⚠️  Falha ao criar keyspace. Verifique se o Cassandra está rodando.")
        return
    
    # Configurar conexão
    if not setup_database():
        print("⚠️  Falha ao conectar ao Cassandra. Verifique se o Cassandra está rodando.")
        return
    
    print("✅ Aplicação iniciada com sucesso!")

@app.get("/")
async def root():
    """Endpoint raiz com informações da API."""
    return {
        "message": "Bem-vindo à CaspyORM Demo API!",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "users": "/users",
            "posts": "/posts"
        }
    }

@app.get("/health")
async def health_check():
    """Verificação de saúde da aplicação."""
    try:
        # Testar conexão com banco
        from aplicacao.models.user import User
        count = User.all().count()
        
        return {
            "status": "healthy",
            "database": "connected",
            "user_count": count
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

@app.get("/demo/setup")
async def setup_demo_data():
    """Configura dados de demonstração."""
    try:
        from aplicacao.models.user import User
        from aplicacao.models.post import Post
        import uuid
        
        # Sincronizar tabelas e corrigir tipos
        User.sync_table(auto_apply=True)
        Post.sync_table(auto_apply=True)
        
        # Criar usuários de demonstração
        users_data = [
            {"username": "joao", "email": "joao@example.com", "full_name": "João Silva"},
            {"username": "maria", "email": "maria@example.com", "full_name": "Maria Santos"},
            {"username": "pedro", "email": "pedro@example.com", "full_name": "Pedro Costa"},
            {"username": "ana", "email": "ana@example.com", "full_name": "Ana Oliveira"},
            {"username": "carlos", "email": "carlos@example.com", "full_name": "Carlos Ferreira"},
            {"username": "julia", "email": "julia@example.com", "full_name": "Julia Rodrigues"},
            {"username": "lucas", "email": "lucas@example.com", "full_name": "Lucas Almeida"},
            {"username": "sofia", "email": "sofia@example.com", "full_name": "Sofia Costa"}
        ]
        
        created_users = []
        for user_data in users_data:
            if not User.filter(email=user_data["email"]).exists():
                user = User.create_user(**user_data)
                created_users.append(user)
        
        # Criar posts de demonstração
        posts_created = 0
        if created_users:
            posts_data = [
                {
                    "title": "Primeiro Post",
                    "content": "Este é o primeiro post da demonstração!",
                    "author_id": created_users[0].id,
                    "tags": ["demo", "primeiro"]
                },
                {
                    "title": "Post sobre Tecnologia",
                    "content": "Discussão sobre as últimas tecnologias.",
                    "author_id": created_users[1].id,
                    "tags": ["tecnologia", "inovaçao"]
                },
                {
                    "title": "Dicas de Programação",
                    "content": "Algumas dicas úteis para programadores iniciantes.",
                    "author_id": created_users[2].id,
                    "tags": ["programaçao", "dicas", "iniciantes"]
                }
            ]
            
            # Adicionar mais posts se houver usuários suficientes
            if len(created_users) > 3:
                posts_data.extend([
                    {
                        "title": "Machine Learning Básico",
                        "content": "Introdução aos conceitos fundamentais de Machine Learning.",
                        "author_id": created_users[3].id,
                        "tags": ["machine-learning", "ai", "tutorial"]
                    },
                    {
                        "title": "Desenvolvimento Web Moderno",
                        "content": "Tecnologias e frameworks para desenvolvimento web em 2024.",
                        "author_id": created_users[4].id,
                        "tags": ["web", "frontend", "backend", "frameworks"]
                    }
                ])
            
            if len(created_users) > 5:
                posts_data.extend([
                    {
                        "title": "DevOps na Prática",
                        "content": "Como implementar práticas DevOps em projetos reais.",
                        "author_id": created_users[5].id,
                        "tags": ["devops", "ci-cd", "deploy"]
                    },
                    {
                        "title": "Segurança em Aplicações Web",
                        "content": "Principais vulnerabilidades e como se proteger.",
                        "author_id": created_users[6].id,
                        "tags": ["segurança", "web", "vulnerabilidades"]
                    }
                ])
            
            if len(created_users) > 7:
                posts_data.append({
                    "title": "Microserviços vs Monolito",
                    "content": "Comparação entre arquiteturas de microserviços e monolito.",
                    "author_id": created_users[7].id,
                    "tags": ["arquitetura", "microserviços", "monolito"]
                })
            
            for post_data in posts_data:
                if not Post.filter(title=post_data["title"]).exists():
                    Post.create_post(**post_data)
                    posts_created += 1
        
        return {
            "message": "Dados de demonstração configurados com sucesso!",
            "users_created": len(created_users),
            "posts_created": posts_created,
            "total_users": User.all().count(),
            "total_posts": Post.all().count()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao configurar dados: {str(e)}")

@app.get("/demo/test")
async def test_endpoints():
    """Testa todos os endpoints principais da API."""
    try:
        from aplicacao.models.user import User
        from aplicacao.models.post import Post
        import uuid
        
        results = {
            "status": "success",
            "tests": {}
        }
        
        # Teste 1: Contagem de usuários e posts
        try:
            user_count = User.all().count()
            post_count = Post.all().count()
            results["tests"]["counts"] = {
                "status": "passed",
                "users": user_count,
                "posts": post_count
            }
        except Exception as e:
            results["tests"]["counts"] = {"status": "failed", "error": str(e)}
        
        # Teste 2: Buscar primeiro usuário
        try:
            first_user = User.all().first()
            if first_user:
                results["tests"]["get_user"] = {
                    "status": "passed",
                    "user_id": str(first_user.id),
                    "username": first_user.username
                }
            else:
                results["tests"]["get_user"] = {"status": "failed", "error": "Nenhum usuário encontrado"}
        except Exception as e:
            results["tests"]["get_user"] = {"status": "failed", "error": str(e)}
        
        # Teste 3: Buscar posts por autor
        try:
            if first_user:
                user_posts = Post.filter(author_id=first_user.id).all()
                results["tests"]["posts_by_author"] = {
                    "status": "passed",
                    "author_id": str(first_user.id),
                    "posts_count": len(user_posts)
                }
            else:
                results["tests"]["posts_by_author"] = {"status": "skipped", "reason": "Nenhum usuário disponível"}
        except Exception as e:
            results["tests"]["posts_by_author"] = {"status": "failed", "error": str(e)}
        
        # Teste 4: Filtrar usuários ativos
        try:
            active_users = User.filter(is_active=True).all()
            results["tests"]["active_users"] = {
                "status": "passed",
                "count": len(active_users)
            }
        except Exception as e:
            results["tests"]["active_users"] = {"status": "failed", "error": str(e)}
        
        # Teste 5: Filtrar posts publicados
        try:
            published_posts = Post.filter(is_published=True).all()
            results["tests"]["published_posts"] = {
                "status": "passed",
                "count": len(published_posts)
            }
        except Exception as e:
            results["tests"]["published_posts"] = {"status": "failed", "error": str(e)}
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro nos testes: {str(e)}")

@app.get("/demo/stats")
async def get_demo_stats():
    """Retorna estatísticas detalhadas dos dados de demonstração."""
    try:
        from aplicacao.models.user import User
        from aplicacao.models.post import Post
        
        # Estatísticas de usuários
        total_users = User.all().count()
        active_users = User.filter(is_active=True).count()
        inactive_users = total_users - active_users
        
        # Estatísticas de posts
        total_posts = Post.all().count()
        published_posts = Post.filter(is_published=True).count()
        draft_posts = total_posts - published_posts
        
        # Posts por autor
        posts_by_author = {}
        users = User.all().all()
        for user in users:
            user_posts = Post.filter(author_id=user.id).count()
            posts_by_author[user.username] = user_posts
        
        # Tags mais populares
        all_posts = Post.all().all()
        tag_count = {}
        for post in all_posts:
            for tag in post.tags:
                tag_count[tag] = tag_count.get(tag, 0) + 1
        
        # Top 5 tags
        top_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "inactive": inactive_users,
                "posts_by_author": posts_by_author
            },
            "posts": {
                "total": total_posts,
                "published": published_posts,
                "draft": draft_posts,
                "top_tags": dict(top_tags)
            },
            "database": {
                "keyspace": "caspyorm_demo",
                "tables": ["users", "posts"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

@app.post("/demo/clean")
async def clean_demo_data():
    """Remove todos os dados de demonstração."""
    try:
        from aplicacao.models.user import User
        from aplicacao.models.post import Post
        
        # Contar antes de deletar
        user_count = User.all().count()
        post_count = Post.all().count()
        
        # Deletar todos os posts primeiro (devido à dependência com usuários)
        posts = Post.all().all()
        for post in posts:
            post.delete()
        
        # Deletar todos os usuários
        users = User.all().all()
        for user in users:
            user.delete()
        
        return {
            "message": "Dados de demonstração removidos com sucesso!",
            "deleted": {
                "users": user_count,
                "posts": post_count
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar dados: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 