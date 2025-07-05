"""
Router para endpoints de usuários.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import uuid

from aplicacao.models.user import User, UserPydantic, UserResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse)
async def create_user(user_data: UserPydantic):
    """Cria um novo usuário."""
    try:
        # Verificar se email já existe
        if User.filter(email=user_data.email).exists():
            raise HTTPException(status_code=400, detail="Email já cadastrado")
        
        # Verificar se username já existe
        if User.filter(username=user_data.username).exists():
            raise HTTPException(status_code=400, detail="Username já cadastrado")
        
        user = User.create_user(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name
        )
        
        return user.to_pydantic_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    active_only: bool = Query(True)
):
    """Lista usuários com paginação."""
    try:
        query = User.all()
        
        if active_only:
            query = query.filter(is_active=True)
        
        # Usar paginação para grandes datasets
        if limit > 50:
            results, _ = query.page(page_size=limit)
        else:
            results = query.limit(limit).all()
        
        return [user.to_pydantic_model() for user in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Busca um usuário por ID."""
    try:
        user = User.get(id=uuid.UUID(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        return user.to_pydantic_model()
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/email/{email}", response_model=UserResponse)
async def get_user_by_email(email: str):
    """Busca um usuário por email."""
    try:
        user = User.filter(email=email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        return user.to_pydantic_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}/tags")
async def update_user_tags(user_id: str, tags: List[str]):
    """Atualiza as tags do usuário de forma atômica."""
    try:
        user = User.get(id=uuid.UUID(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Atualizar tags de forma atômica
        user.update_collection('tags', add=tags)
        
        return {"message": "Tags atualizadas com sucesso"}
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/count")
async def get_user_count():
    """Retorna o número total de usuários (otimizado)."""
    try:
        total = User.all().count()
        active = User.filter(is_active=True).count()
        
        return {
            "total_users": total,
            "active_users": active,
            "inactive_users": total - active
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test/bulk")
async def test_bulk_operations():
    """Testa operações em lote com usuários."""
    try:
        # Criar múltiplos usuários de teste
        test_users = []
        for i in range(5):
            user_data = {
                "username": f"test_user_{i}",
                "email": f"test{i}@example.com",
                "full_name": f"Usuário Teste {i}"
            }
            
            if not User.filter(email=user_data["email"]).exists():
                user = User.create_user(**user_data)
                test_users.append(user)
        
        # Testar atualização em lote
        updated_count = 0
        for user in test_users:
            user.update(tags=["test", "bulk"])
            updated_count += 1
        
        return {
            "message": "Operações em lote testadas com sucesso",
            "created": len(test_users),
            "updated": updated_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test/search")
async def test_search_operations():
    """Testa operações de busca e filtros."""
    try:
        results = {}
        
        # Buscar por email
        try:
            user_by_email = User.filter(email="joao@example.com").first()
            results["email_search"] = {
                "status": "success",
                "found": user_by_email is not None,
                "username": user_by_email.username if user_by_email else None
            }
        except Exception as e:
            results["email_search"] = {"status": "error", "message": str(e)}
        
        # Buscar usuários com tags
        try:
            users_with_tags = User.all().all()
            users_with_tags = [u for u in users_with_tags if u.tags]
            results["users_with_tags"] = {
                "status": "success",
                "count": len(users_with_tags)
            }
        except Exception as e:
            results["users_with_tags"] = {"status": "error", "message": str(e)}
        
        # Testar paginação
        try:
            all_users = User.all().all()
            paginated = all_users[:3]  # Primeiros 3
            results["pagination"] = {
                "status": "success",
                "total": len(all_users),
                "paginated_count": len(paginated)
            }
        except Exception as e:
            results["pagination"] = {"status": "error", "message": str(e)}
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 