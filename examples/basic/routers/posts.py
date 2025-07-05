"""
Router para endpoints de posts.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
import uuid

from aplicacao.models.post import Post, PostPydantic, PostResponse
from aplicacao.models.user import User

router = APIRouter(prefix="/posts", tags=["posts"])

@router.post("/", response_model=PostResponse)
async def create_post(post_data: PostPydantic):
    """Cria um novo post."""
    try:
        # Verificar se o autor existe
        author = User.get(id=post_data.author_id)
        if not author:
            raise HTTPException(status_code=404, detail="Autor não encontrado")
        
        post = Post.create_post(
            title=post_data.title,
            content=post_data.content,
            author_id=post_data.author_id,
            tags=post_data.tags
        )
        
        return post.to_pydantic_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[PostResponse])
async def list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    published_only: bool = Query(True)
):
    """Lista posts com paginação."""
    try:
        query = Post.all()
        
        if published_only:
            query = query.filter(is_published=True)
        
        # Usar paginação para grandes datasets
        if limit > 50:
            results, _ = query.page(page_size=limit)
        else:
            results = query.limit(limit).all()
        
        return [post.to_pydantic_model() for post in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: str):
    """Busca um post por ID."""
    try:
        post = Post.get(id=uuid.UUID(post_id))
        if not post:
            raise HTTPException(status_code=404, detail="Post não encontrado")
        
        return post.to_pydantic_model()
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/author/{author_id}", response_model=List[PostResponse])
async def get_posts_by_author(author_id: str):
    """Busca posts por autor."""
    try:
        posts = Post.filter(author_id=uuid.UUID(author_id)).all()
        return [post.to_pydantic_model() for post in posts]
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{post_id}/like")
async def like_post(post_id: str, user_id: str):
    """Adiciona um like ao post de forma atômica."""
    try:
        post = Post.get(id=uuid.UUID(post_id))
        if not post:
            raise HTTPException(status_code=404, detail="Post não encontrado")
        
        # Verificar se usuário existe
        user = User.get(id=uuid.UUID(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Adicionar like de forma atômica
        post.add_like(uuid.UUID(user_id))
        
        return {"message": "Like adicionado com sucesso"}
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{post_id}/like")
async def unlike_post(post_id: str, user_id: str):
    """Remove um like do post de forma atômica."""
    try:
        post = Post.get(id=uuid.UUID(post_id))
        if not post:
            raise HTTPException(status_code=404, detail="Post não encontrado")
        
        # Remover like de forma atômica
        post.remove_like(uuid.UUID(user_id))
        
        return {"message": "Like removido com sucesso"}
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{post_id}/tags")
async def update_post_tags(post_id: str, tags: List[str]):
    """Atualiza as tags do post de forma atômica."""
    try:
        post = Post.get(id=uuid.UUID(post_id))
        if not post:
            raise HTTPException(status_code=404, detail="Post não encontrado")
        
        # Atualizar tags de forma atômica
        for tag in tags:
            post.add_tag(tag)
        
        return {"message": "Tags atualizadas com sucesso"}
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/count")
async def get_post_count():
    """Retorna estatísticas de posts (otimizado)."""
    try:
        total = Post.all().count()
        published = Post.filter(is_published=True).count()
        
        return {
            "total_posts": total,
            "published_posts": published,
            "draft_posts": total - published
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test/likes")
async def test_like_operations():
    """Testa operações de like em posts."""
    try:
        # Buscar primeiro post
        first_post = Post.all().first()
        if not first_post:
            raise HTTPException(status_code=404, detail="Nenhum post encontrado para teste")
        
        # Buscar primeiro usuário
        first_user = User.all().first()
        if not first_user:
            raise HTTPException(status_code=404, detail="Nenhum usuário encontrado para teste")
        
        # Adicionar like
        first_post.add_like(first_user.id)
        
        # Verificar se o like foi adicionado
        post_after_like = Post.get(id=first_post.id)
        likes_count = len(post_after_like.likes)
        
        # Remover like
        first_post.remove_like(first_user.id)
        
        # Verificar se o like foi removido
        post_after_unlike = Post.get(id=first_post.id)
        likes_count_after = len(post_after_unlike.likes)
        
        return {
            "message": "Operações de like testadas com sucesso",
            "post_id": str(first_post.id),
            "user_id": str(first_user.id),
            "likes_after_add": likes_count,
            "likes_after_remove": likes_count_after
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test/tags")
async def test_tag_operations():
    """Testa operações de tags em posts."""
    try:
        # Buscar primeiro post
        first_post = Post.all().first()
        if not first_post:
            raise HTTPException(status_code=404, detail="Nenhum post encontrado para teste")
        
        # Adicionar tags
        test_tags = ["test", "automated", "caspyorm"]
        for tag in test_tags:
            first_post.add_tag(tag)
        
        # Verificar tags
        post_after_tags = Post.get(id=first_post.id)
        current_tags = post_after_tags.tags
        
        return {
            "message": "Operações de tags testadas com sucesso",
            "post_id": str(first_post.id),
            "added_tags": test_tags,
            "current_tags": current_tags
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test/collections")
async def test_collection_operations():
    """Testa operações com coleções (list, set, map)."""
    try:
        results = {}
        
        # Testar posts com tags
        try:
            posts_with_tags = Post.all().all()
            posts_with_tags = [p for p in posts_with_tags if p.tags]
            results["posts_with_tags"] = {
                "status": "success",
                "count": len(posts_with_tags),
                "sample_tags": posts_with_tags[0].tags if posts_with_tags else []
            }
        except Exception as e:
            results["posts_with_tags"] = {"status": "error", "message": str(e)}
        
        # Testar posts com likes
        try:
            posts_with_likes = Post.all().all()
            posts_with_likes = [p for p in posts_with_likes if p.likes]
            results["posts_with_likes"] = {
                "status": "success",
                "count": len(posts_with_likes),
                "sample_likes_count": len(posts_with_likes[0].likes) if posts_with_likes else 0
            }
        except Exception as e:
            results["posts_with_likes"] = {"status": "error", "message": str(e)}
        
        # Testar usuários com preferências
        try:
            users_with_prefs = User.all().all()
            users_with_prefs = [u for u in users_with_prefs if u.preferences]
            results["users_with_preferences"] = {
                "status": "success",
                "count": len(users_with_prefs)
            }
        except Exception as e:
            results["users_with_preferences"] = {"status": "error", "message": str(e)}
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 