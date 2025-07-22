"""
Testes de Integração Assíncronos com Cassandra Real
==================================================

Estes testes validam o comportamento assíncrono do CaspyORM usando
o Cassandra real, não mocks. Eles testam:

1. Operações CRUD assíncronas reais
2. Validação de chaves primárias com UUID automático
3. Timeouts em operações assíncronas
4. Campos complexos (List, Set, Map)
5. Performance e concorrência
"""

import pytest
import asyncio
import uuid
from datetime import datetime
from typing import List, Set, Dict

from cassandra.cluster import Cluster
from caspyorm import Model
from caspyorm.fields import Text, Integer, UUID, Timestamp, List as ListField, Set as SetField, Map as MapField
from caspyorm.exceptions import ValidationError, CaspyORMException
from caspyorm.connection import connect, get_async_session


class UserReal(Model):
    """Modelo de usuário para testes com Cassandra real."""
    __table_name__ = "users_real_test"
    
    id = UUID(primary_key=True)  # UUID automático
    name = Text(required=True)
    email = Text(index=True)
    age = Integer()
    created_at = Timestamp(default=datetime.now)
    tags = ListField(Text())
    roles = SetField(Text())
    metadata = MapField(Text(), Text())


class ProductReal(Model):
    """Modelo de produto para testes de concorrência."""
    __table_name__ = "products_real_test"
    
    id = UUID(primary_key=True)
    name = Text(required=True)
    price = Integer(required=True)
    category = Text(index=True)
    in_stock = Integer(default=0)


@pytest.fixture(scope="session")
def setup_cassandra():
    """Configura conexão com Cassandra real para testes."""
    connect(
        contact_points=['127.0.0.1'],
        port=9042,
        keyspace='caspyorm_test_suite'
    )
    
    # Sincronizar tabelas
    UserReal.sync_table()
    ProductReal.sync_table()
    
    yield
    
    # Cleanup (opcional - as tabelas podem ser mantidas para debug)


@pytest.fixture(autouse=True)
def clean_tables():
    """Limpa as tabelas de teste antes de cada teste async."""
    cluster = Cluster(["127.0.0.1"], port=9042)
    session = cluster.connect("caspyorm_test_suite")
    session.execute("TRUNCATE users_real_test;")
    session.execute("TRUNCATE products_real_test;")
    cluster.shutdown()


@pytest.mark.asyncio
class TestAsyncCassandraReal:
    """Testes assíncronos com Cassandra real."""
    
    async def test_save_async_with_uuid_auto_generation(self, setup_cassandra, clean_tables):
        UserReal.sync_table(auto_apply=True)
        ProductReal.sync_table(auto_apply=True)
        """Testa salvamento assíncrono com UUID gerado automaticamente."""
        # Criar usuário sem especificar ID (deve ser gerado automaticamente)
        user = UserReal(
            name="João Silva",
            email="joao@example.com",
            age=30,
            tags=["desenvolvedor", "python"],
            roles={"user", "admin"},
            metadata={"department": "engineering", "level": "senior"}
        )
        
        # Verificar que o ID foi gerado automaticamente durante a criação
        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        
        # Salvar assincronamente
        await user.save_async()
        
        # Verificar que o ID permanece o mesmo após o salvamento
        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        
        # Buscar o usuário para confirmar que foi salvo
        saved_user = await UserReal.get_async(id=user.id)
        assert saved_user is not None
        assert saved_user.name == "João Silva"
        assert saved_user.email == "joao@example.com"
        assert saved_user.age == 30
        assert saved_user.tags == ["desenvolvedor", "python"]
        assert saved_user.roles == {"user", "admin"}
        assert saved_user.metadata == {"department": "engineering", "level": "senior"}
    
    async def test_save_async_with_custom_uuid(self, setup_cassandra, clean_tables):
        UserReal.sync_table(auto_apply=True)
        ProductReal.sync_table(auto_apply=True)
        """Testa salvamento assíncrono com UUID customizado."""
        custom_id = uuid.uuid4()
        user = UserReal(
            id=custom_id,
            name="Maria Santos",
            email="maria@example.com",
            age=25
        )
        
        await user.save_async()
        
        # Verificar que o ID customizado foi mantido
        assert user.id == custom_id
        
        # Buscar para confirmar
        saved_user = await UserReal.get_async(id=custom_id)
        assert saved_user is not None
        assert saved_user.id == custom_id  # type: ignore[attr-defined]
        assert saved_user.name == "Maria Santos"  # type: ignore[attr-defined]
        assert saved_user.email == "maria@example.com"  # type: ignore[attr-defined]
        assert saved_user.age == 25  # type: ignore[attr-defined]
    
    async def test_save_async_without_required_field(self, setup_cassandra, clean_tables):
        UserReal.sync_table(auto_apply=True)
        ProductReal.sync_table(auto_apply=True)
        """Testa erro ao salvar sem campo obrigatório."""
        import pytest
        from caspyorm.exceptions import ValidationError
        with pytest.raises(ValidationError, match="Campo 'name' é obrigatório"):
            user = UserReal(
                id=uuid.uuid4(),  # type: ignore[attr-defined]
                # name está faltando (campo obrigatório)
                email="test@example.com"  # type: ignore[attr-defined]
            )
            await user.save_async()
    
    async def test_update_async_real(self, setup_cassandra, clean_tables):
        UserReal.sync_table(auto_apply=True)
        ProductReal.sync_table(auto_apply=True)
        """Testa atualização assíncrona real."""
        # Criar usuário
        user = UserReal(
            name="Pedro Costa",
            email="pedro@example.com",
            age=35
        )
        await user.save_async()
        
        # Atualizar
        updated_user = await user.update_async(
            age=36,
            tags=["manager", "leader"]
        )
        
        assert updated_user.age == 36
        assert updated_user.tags == ["manager", "leader"]
        
        # Verificar no banco
        saved_user = await UserReal.get_async(id=user.id)
        assert saved_user.age == 36
        assert saved_user.tags == ["manager", "leader"]
    
    async def test_delete_async_real(self, setup_cassandra, clean_tables):
        UserReal.sync_table(auto_apply=True)
        ProductReal.sync_table(auto_apply=True)
        """Testa deleção assíncrona real."""
        # Criar usuário
        user = UserReal(
            name="Ana Silva",
            email="ana@example.com",
            age=28
        )
        await user.save_async()
        
        # Verificar que existe
        saved_user = await UserReal.get_async(id=user.id)
        assert saved_user is not None
        
        # Deletar
        await user.delete_async()
        
        # Verificar que foi deletado
        deleted_user = await UserReal.get_async(id=user.id)
        assert deleted_user is None
    
    async def test_filter_async_real(self, setup_cassandra, clean_tables):
        UserReal.sync_table(auto_apply=True)
        ProductReal.sync_table(auto_apply=True)
        """Testa filtros assíncronos reais."""
        # Criar múltiplos usuários
        users_data = [
            ("Carlos", "carlos@example.com", 40, []),
            ("Diana", "diana@example.com", 32, ["python", "async"]),
            ("Eduardo", "eduardo@example.com", 40, []),
        ]

        created_users = []
        for name, email, age, tags in users_data:
            user = UserReal(name=name, email=email, age=age, tags=tags)
            await user.save_async()
            created_users.append(user)
        
        # Buscar todos os usuários (sem filtros)
        all_users = await UserReal.all().all_async()
        assert len(all_users) >= 3
        
        # Verificar que os usuários foram criados
        user_names = [user.name for user in all_users]
        assert "Carlos" in user_names
        assert "Diana" in user_names
        assert "Eduardo" in user_names
        
        # Buscar usuário específico por ID (chave primária)
        diana_id = None
        for user in all_users:
            if user.name == "Diana":
                diana_id = user.id
                break
        
        assert diana_id is not None
        diana = await UserReal.get_async(id=diana_id)
        assert diana is not None
        assert diana.name == "Diana"  # type: ignore[attr-defined]
        assert diana.age == 32  # type: ignore[attr-defined]
        assert diana.tags == ["python", "async"]  # type: ignore[attr-defined]
    
    async def test_bulk_create_async_real(self, setup_cassandra, clean_tables):
        UserReal.sync_table(auto_apply=True)
        ProductReal.sync_table(auto_apply=True)
        """Testa criação em lote assíncrona real."""
        users_data = [
            {"name": "Felipe", "email": "felipe@example.com", "age": 29},
            {"name": "Gabriela", "email": "gabriela@example.com", "age": 31},
            {"name": "Henrique", "email": "henrique@example.com", "age": 27},
        ]
        
        # Criar em lote
        users = await UserReal.bulk_create_async(users_data)
        
        assert len(users) == 3
        assert all(user.id is not None for user in users)
        assert all(isinstance(user.id, uuid.UUID) for user in users)
        
        # Verificar que todos foram salvos
        for user in users:
            saved_user = await UserReal.get_async(id=user.id)
            assert saved_user is not None
            assert saved_user.name in ["Felipe", "Gabriela", "Henrique"]
    
    async def test_complex_fields_async(self, setup_cassandra, clean_tables):
        UserReal.sync_table(auto_apply=True)
        ProductReal.sync_table(auto_apply=True)
        """Testa campos complexos (List, Set, Map) assíncronos."""
        user = UserReal(
            name="Isabela",
            email="isabela@example.com",
            age=26,
            tags=["designer", "ui", "ux"],
            roles={"designer", "team_lead"},
            metadata={
                "skills": "design, prototyping",
                "experience": "5 years",
                "tools": "figma, sketch"
            }
        )
        
        await user.save_async()
        
        # Verificar campos complexos
        saved_user = await UserReal.get_async(id=user.id)
        assert saved_user.tags == ["designer", "ui", "ux"]
        assert saved_user.roles == {"designer", "team_lead"}
        assert saved_user.metadata == {
            "skills": "design, prototyping",
            "experience": "5 years",
            "tools": "figma, sketch"
        }
    
    async def test_concurrent_operations(self, setup_cassandra, clean_tables):
        UserReal.sync_table(auto_apply=True)
        ProductReal.sync_table(auto_apply=True)
        """Testa operações concorrentes assíncronas."""
        # Criar múltiplos produtos
        products_data = [
            {"name": "Laptop", "price": 1500, "category": "electronics", "in_stock": 10},
            {"name": "Mouse", "price": 50, "category": "electronics", "in_stock": 100},
            {"name": "Keyboard", "price": 100, "category": "electronics", "in_stock": 50},
        ]
        
        # Criar produtos em paralelo
        tasks = []
        for data in products_data:
            product = ProductReal(**data)
            tasks.append(product.save_async())
        
        await asyncio.gather(*tasks)
        
        # Buscar todos os produtos
        products = await ProductReal.filter(category="electronics").all_async()
        assert len(products) == 3
        
        # Atualizar estoque em paralelo
        update_tasks = []
        for product in products:
            update_tasks.append(product.update_async(in_stock=product.in_stock + 5))
        
        await asyncio.gather(*update_tasks)
        
        # Verificar atualizações
        updated_products = await ProductReal.filter(category="electronics").all_async()
        for product in updated_products:
            if product.name == "Laptop":
                assert product.in_stock == 15
            elif product.name == "Mouse":
                assert product.in_stock == 105  # type: ignore[attr-defined]
            elif product.name == "Keyboard":  # type: ignore[attr-defined]
                assert product.in_stock == 55  # type: ignore[attr-defined]
    
    async def test_timeout_handling(self, setup_cassandra, clean_tables):
        UserReal.sync_table(auto_apply=True)
        ProductReal.sync_table(auto_apply=True)
        """Testa tratamento de timeout em operações assíncronas."""
        import pytest
        from caspyorm.exceptions import CaspyORMException
        import asyncio
        user = UserReal(
            name="Timeout Test",
            email="timeout@example.com",
            age=30
        )
        # Simular operação lenta
        original_save_instance_async = user.save_async
        async def slow_save(*args, **kwargs):
            await asyncio.sleep(1)
            return await original_save_instance_async(*args, **kwargs)
        user.save_async = slow_save  # type: ignore
        with pytest.raises(CaspyORMException, match="Database operation timed out"):
            await user.save_async(timeout=0.001)  # 1ms timeout
    
    async def test_error_handling_real(self, setup_cassandra, clean_tables):
        UserReal.sync_table(auto_apply=True)
        ProductReal.sync_table(auto_apply=True)
        """Testa tratamento de erros reais."""
        import pytest
        with pytest.raises(TypeError, match="Não foi possível converter 'not_a_number' para int"):
            user = UserReal(
                name="Error Test",
                email="error@example.com",
                age="not_a_number"  # Deveria ser int
            )
            await user.save_async()
    
    async def test_performance_metrics(self, setup_cassandra, clean_tables):
        UserReal.sync_table(auto_apply=True)
        ProductReal.sync_table(auto_apply=True)
        """Testa métricas de performance de operações assíncronas."""
        import time
        
        # Medir tempo de criação
        start_time = time.time()
        
        users = []
        for i in range(10):
            user = UserReal(
                name=f"User {i}",
                email=f"user{i}@example.com",
                age=20 + i
            )
            users.append(user)
        
        # Criar em paralelo
        await asyncio.gather(*[user.save_async() for user in users])
        
        creation_time = time.time() - start_time
        
        # Medir tempo de busca
        start_time = time.time()
        all_users = await UserReal.all().all_async()
        query_time = time.time() - start_time
        
        assert len(all_users) >= 10
        assert creation_time < 5.0  # Deve ser rápido
        assert query_time < 2.0     # Deve ser muito rápido
        
        print(f"Creation time: {creation_time:.3f}s")
        print(f"Query time: {query_time:.3f}s")


@pytest.mark.asyncio
class TestAsyncSchemaOperations:
    """Testes de operações de schema assíncronas."""
    
    async def test_sync_table_async_real(self, setup_cassandra, clean_tables):
        """Testa sincronização de tabela assíncrona real."""
        # Criar modelo dinâmico
        DynamicUser = Model.create_model(
            name="DynamicUser",
            fields={
                "id": UUID(primary_key=True),
                "name": Text(required=True),
                "score": Integer(default=0)
            },
            table_name="dynamic_users_real_test"
        )
        
        # Sincronizar tabela
        await DynamicUser.sync_table_async()
        
        # Criar instância
        user = DynamicUser(name="Dynamic User")
        await user.save_async()
        
        # Verificar que foi salvo
        saved_user = await DynamicUser.get_async(id=user.id)
        assert saved_user is not None
        assert saved_user.name == "Dynamic User"
        assert saved_user.score == 0  # valor padrão


if __name__ == "__main__":
    # Executar testes individualmente para debug
    pytest.main([__file__, "-v", "-s"]) 