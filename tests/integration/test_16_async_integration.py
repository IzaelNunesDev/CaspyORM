"""
Testes de integração assíncronos para CaspyORM.

Este módulo testa operações CRUD assíncronas usando a sessão real do Cassandra
para validar a interação com o cassandra-driver de forma assíncrona.
"""

import pytest
import asyncio
import uuid
from datetime import datetime
from typing import List, Optional

from caspyorm.model import Model
from caspyorm.fields import Text, Integer, UUID, Timestamp, Boolean, List as ListField, Set as SetField
from caspyorm.connection import get_async_session, connect_async
from caspyorm.query import QuerySet


class AsyncTestUser(Model):
    """Modelo de teste para operações assíncronas."""
    __table_name__ = "async_test_users"
    
    id = UUID(primary_key=True)
    name = Text()
    email = Text()
    age = Integer()
    is_active = Boolean(default=True)
    created_at = Timestamp()
    tags = ListField(Text())
    permissions = SetField(Text())


class AsyncTestPost(Model):
    """Modelo de teste para relacionamentos."""
    __table_name__ = "async_test_posts"
    
    id = UUID(primary_key=True)
    user_id = UUID()  # Referência ao usuário
    title = Text()
    content = Text()
    published = Boolean(default=False)
    created_at = Timestamp()


@pytest.fixture(scope="module")
async def setup_database():
    """Configura o banco de dados para os testes."""
    # Conectar ao Cassandra
    await connect_async(
        contact_points=['localhost'],
        keyspace='test_keyspace',
        port=9042
    )
    
    # Sincronizar tabelas
    await AsyncTestUser.sync_table_async()
    await AsyncTestPost.sync_table_async()
    
    yield
    
    # Limpeza após os testes
    session = get_async_session()
    if session:
        import asyncio
        await asyncio.to_thread(session.execute, "DROP TABLE IF EXISTS async_test_users")
        await asyncio.to_thread(session.execute, "DROP TABLE IF EXISTS async_test_posts")


@pytest.mark.asyncio
class TestAsyncCRUDOperations:
    """Testes para operações CRUD assíncronas."""
    
    async def test_create_async(self, setup_database):
        """Testa criação assíncrona de modelo."""
        user_id = uuid.uuid4()
        user = AsyncTestUser(
            id=user_id,
            name="John Doe",
            email="john@example.com",
            age=30,
            created_at=datetime.now(),
            tags=["admin", "user"],
            permissions={"read", "write"}
        )
        
        await user.save_async()
        
        # Verificar se foi salvo
        saved_user = await AsyncTestUser.get_async(id=user_id)
        assert saved_user is not None
        assert saved_user.name == "John Doe"
        assert saved_user.email == "john@example.com"
        assert saved_user.age == 30
        assert saved_user.tags == ["admin", "user"]
        assert saved_user.permissions == {"read", "write"}
    
    async def test_get_async(self, setup_database):
        """Testa busca assíncrona de modelo."""
        user_id = uuid.uuid4()
        user = AsyncTestUser(
            id=user_id,
            name="Jane Smith",
            email="jane@example.com",
            age=25,
            created_at=datetime.now(),
            tags=["user"],
            permissions={"read"}
        )
        await user.save_async()
        
        # Buscar o usuário
        found_user = await AsyncTestUser.get_async(id=user_id)
        assert found_user is not None
        assert found_user.name == "Jane Smith"
        assert found_user.email == "jane@example.com"
    
    async def test_get_async_not_found(self, setup_database):
        """Testa busca assíncrona de modelo inexistente."""
        non_existent_id = uuid.uuid4()
        user = await AsyncTestUser.get_async(id=non_existent_id)
        assert user is None
    
    async def test_update_async(self, setup_database):
        """Testa atualização assíncrona de modelo."""
        user_id = uuid.uuid4()
        user = AsyncTestUser(
            id=user_id,
            name="Bob Wilson",
            email="bob@example.com",
            age=35,
            created_at=datetime.now(),
            tags=["user"],
            permissions={"read"}
        )
        await user.save_async()
        
        # Atualizar o usuário
        user.name = "Bob Johnson"
        user.age = 36
        user.tags.append("vip")
        await user.save_async()
        
        # Verificar se foi atualizado
        updated_user = await AsyncTestUser.get_async(id=user_id)
        assert updated_user.name == "Bob Johnson"
        assert updated_user.age == 36
        assert "vip" in updated_user.tags
    
    async def test_delete_async(self, setup_database):
        """Testa deleção assíncrona de modelo."""
        user_id = uuid.uuid4()
        user = AsyncTestUser(
            id=user_id,
            name="Alice Brown",
            email="alice@example.com",
            age=28,
            created_at=datetime.now(),
            tags=["user"],
            permissions={"read"}
        )
        await user.save_async()
        
        # Verificar se foi salvo
        saved_user = await AsyncTestUser.get_async(id=user_id)
        assert saved_user is not None
        
        # Deletar o usuário
        await user.delete_async()
        
        # Verificar se foi deletado
        deleted_user = await AsyncTestUser.get_async(id=user_id)
        assert deleted_user is None
    
    async def test_bulk_create_async(self, setup_database):
        """Testa criação em lote assíncrona."""
        users = []
        for i in range(5):
            user = AsyncTestUser(
                id=uuid.uuid4(),
                name=f"User {i}",
                email=f"user{i}@example.com",
                age=20 + i,
                created_at=datetime.now(),
                tags=[f"tag{i}"],
                permissions={"read"}
            )
            users.append(user)
        
        # Criar em lote
        created_users = await AsyncTestUser.bulk_create_async(users)
        assert len(created_users) == 5
        
        # Verificar se todos foram criados
        for user in created_users:
            saved_user = await AsyncTestUser.get_async(id=user.id)
            assert saved_user is not None
            assert saved_user.name == user.name
            assert saved_user.email == user.email


@pytest.mark.asyncio
class TestAsyncQuerySet:
    """Testes para QuerySet assíncrono."""
    
    async def test_all_async(self, setup_database):
        """Testa QuerySet.all_async()."""
        # Criar alguns usuários
        users = []
        for i in range(3):
            user = AsyncTestUser(
                id=uuid.uuid4(),
                name=f"QueryUser {i}",
                email=f"query{i}@example.com",
                age=25 + i,
                created_at=datetime.now(),
                tags=["query_test"],
                permissions={"read"}
            )
            await user.save_async()
            users.append(user)
        
        # Buscar todos
        all_users = await AsyncTestUser.objects.all_async()
        assert len(all_users) >= 3
        
        # Verificar se nossos usuários estão na lista
        user_ids = {user.id for user in users}
        found_ids = {user.id for user in all_users if user.name.startswith("QueryUser")}
        assert user_ids.issubset(found_ids)
    
    async def test_filter_async(self, setup_database):
        """Testa QuerySet.filter_async()."""
        # Criar usuários com diferentes idades
        young_user = AsyncTestUser(
            id=uuid.uuid4(),
            name="Young User",
            email="young@example.com",
            age=18,
            created_at=datetime.now(),
            tags=["young"],
            permissions={"read"}
        )
        await young_user.save_async()
        
        old_user = AsyncTestUser(
            id=uuid.uuid4(),
            name="Old User",
            email="old@example.com",
            age=65,
            created_at=datetime.now(),
            tags=["old"],
            permissions={"read"}
        )
        await old_user.save_async()
        
        # Filtrar por idade
        young_users = await AsyncTestUser.objects.filter_async(age__lt=30).allow_filtering().all_async()
        assert len(young_users) >= 1
        assert all(user.age < 30 for user in young_users)
        
        old_users = await AsyncTestUser.objects.filter_async(age__gt=60).allow_filtering().all_async()
        assert len(old_users) >= 1
        assert all(user.age > 60 for user in old_users)
    
    async def test_first_async(self, setup_database):
        """Testa QuerySet.first_async()."""
        user_id = uuid.uuid4()
        user = AsyncTestUser(
            id=user_id,
            name="First User",
            email="first@example.com",
            age=30,
            created_at=datetime.now(),
            tags=["first"],
            permissions={"read"}
        )
        await user.save_async()
        
        # Buscar primeiro
        first_user = await AsyncTestUser.objects.filter_async(id=user_id).first_async()
        assert first_user is not None
        assert first_user.id == user_id
        assert first_user.name == "First User"
    
    async def test_count_async(self, setup_database):
        """Testa QuerySet.count_async()."""
        # Criar alguns usuários
        for i in range(3):
            user = AsyncTestUser(
                id=uuid.uuid4(),
                name=f"CountUser {i}",
                email=f"count{i}@example.com",
                age=25,
                created_at=datetime.now(),
                tags=["count_test"],
                permissions={"read"}
            )
            await user.save_async()
        
        # Contar usuários com tag específica
        count = await AsyncTestUser.objects.filter_async(tags__contains="count_test").allow_filtering().count_async()
        assert count >= 3
    
    async def test_exists_async(self, setup_database):
        """Testa QuerySet.exists_async()."""
        user_id = uuid.uuid4()
        user = AsyncTestUser(
            id=user_id,
            name="Exists User",
            email="exists@example.com",
            age=30,
            created_at=datetime.now(),
            tags=["exists"],
            permissions={"read"}
        )
        await user.save_async()
        
        # Verificar se existe
        exists = await AsyncTestUser.objects.filter_async(id=user_id).exists_async()
        assert exists is True
        
        # Verificar se não existe
        non_existent_id = uuid.uuid4()
        not_exists = await AsyncTestUser.objects.filter_async(id=non_existent_id).exists_async()
        assert not_exists is False
    
    async def test_delete_async_queryset(self, setup_database):
        """Testa QuerySet.delete_async()."""
        # Criar usuários para deletar
        users_to_delete = []
        for i in range(3):
            user = AsyncTestUser(
                id=uuid.uuid4(),
                name=f"DeleteUser {i}",
                email=f"delete{i}@example.com",
                age=30,
                created_at=datetime.now(),
                tags=["delete_test"],
                permissions={"read"}
            )
            await user.save_async()
            users_to_delete.append(user)
        
        # Verificar se foram criados
        for user in users_to_delete:
            saved_user = await AsyncTestUser.get_async(id=user.id)
            assert saved_user is not None
        
        # Deletar via QuerySet
        deleted_count = await AsyncTestUser.objects.filter_async(tags__contains="delete_test").allow_filtering().delete_async()
        assert deleted_count >= 3
        
        # Verificar se foram deletados
        for user in users_to_delete:
            deleted_user = await AsyncTestUser.get_async(id=user.id)
            assert deleted_user is None
    
    async def test_page_async(self, setup_database):
        """Testa QuerySet.page_async()."""
        # Criar muitos usuários para testar paginação
        for i in range(15):
            user = AsyncTestUser(
                id=uuid.uuid4(),
                name=f"PageUser {i}",
                email=f"page{i}@example.com",
                age=25 + (i % 10),
                created_at=datetime.now(),
                tags=["page_test"],
                permissions={"read"}
            )
            await user.save_async()
        
        # Primeira página
        page1, next_state = await AsyncTestUser.objects.filter_async(tags__contains="page_test").allow_filtering().page_async(page_size=5)
        assert len(page1) == 5
        assert next_state is not None
        
        # Segunda página
        page2, next_state2 = await AsyncTestUser.objects.filter_async(tags__contains="page_test").allow_filtering().page_async(page_size=5, paging_state=next_state)
        assert len(page2) > 0  # Deve ter pelo menos alguns registros
        # next_state2 pode ser None se não houver mais páginas
        
        # Verificar que as páginas são diferentes
        page1_ids = {user.id for user in page1}
        page2_ids = {user.id for user in page2}
        assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
class TestAsyncComplexOperations:
    """Testes para operações complexas assíncronas."""
    
    async def test_transaction_like_operations(self, setup_database):
        """Testa operações que simulam transações."""
        # Criar usuário e posts relacionados
        user_id = uuid.uuid4()
        user = AsyncTestUser(
            id=user_id,
            name="Blog User",
            email="blog@example.com",
            age=30,
            created_at=datetime.now(),
            tags=["blogger"],
            permissions={"read", "write"}
        )
        await user.save_async()
        
        # Criar posts para o usuário
        posts = []
        for i in range(3):
            post = AsyncTestPost(
                id=uuid.uuid4(),
                user_id=user_id,
                title=f"Post {i}",
                content=f"Content for post {i}",
                published=i > 0,  # Primeiro post não publicado
                created_at=datetime.now()
            )
            await post.save_async()
            posts.append(post)
        
        # Buscar usuário com posts
        user_with_posts = await AsyncTestUser.get_async(id=user_id)
        assert user_with_posts is not None
        
        # Buscar posts do usuário
        user_posts = await AsyncTestPost.objects.filter_async(user_id=user_id).allow_filtering().all_async()
        assert len(user_posts) == 3
        
        # Buscar apenas posts publicados
        published_posts = await AsyncTestPost.objects.filter_async(user_id=user_id, published=True).allow_filtering().all_async()
        assert len(published_posts) == 2
    
    async def test_complex_filtering_async(self, setup_database):
        """Testa filtros complexos assíncronos."""
        # Criar usuários com diferentes características
        users_data = [
            {"name": "Admin User", "age": 35, "tags": ["admin", "vip"], "permissions": {"read", "write", "admin"}},
            {"name": "Regular User", "age": 25, "tags": ["user"], "permissions": {"read"}},
            {"name": "VIP User", "age": 40, "tags": ["vip", "premium"], "permissions": {"read", "write"}},
            {"name": "Young User", "age": 18, "tags": ["user", "young"], "permissions": {"read"}},
        ]
        
        for user_data in users_data:
            user = AsyncTestUser(
                id=uuid.uuid4(),
                name=user_data["name"],
                email=f"{user_data['name'].lower().replace(' ', '')}@example.com",
                age=user_data["age"],
                created_at=datetime.now(),
                tags=user_data["tags"],
                permissions=user_data["permissions"]
            )
            await user.save_async()
        
        # Filtros complexos
        # Usuários VIP com mais de 30 anos
        vip_adults = await AsyncTestUser.objects.filter_async(
            tags__contains="vip",
            age__gt=30
        ).allow_filtering().all_async()
        assert len(vip_adults) >= 1
        assert all("vip" in user.tags and user.age > 30 for user in vip_adults)
        
        # Usuários com permissão de escrita
        writers = await AsyncTestUser.objects.filter_async(
            permissions__contains="write"
        ).allow_filtering().all_async()
        assert len(writers) >= 2
        assert all("write" in user.permissions for user in writers)
        
        # Usuários jovens (menos de 25 anos)
        young_users = await AsyncTestUser.objects.filter_async(
            age__lt=25
        ).allow_filtering().all_async()
        assert len(young_users) >= 1
        assert all(user.age < 25 for user in young_users)


if __name__ == "__main__":
    pytest.main([__file__]) 