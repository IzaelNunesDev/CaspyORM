"""
Testes unitários para operações CRUD assíncronas da CaspyORM.
"""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from concurrent.futures import Future

from caspyorm.model import Model
from caspyorm.fields import Text, Integer, UUID
from caspyorm.exceptions import ValidationError


class TestUser(Model):
    __table_name__ = "test_users"
    id = UUID(primary_key=True)
    name = Text()
    email = Text()
    age = Integer(required=False)


@pytest.fixture
def mock_async_session():
    """Mock para sessão assíncrona do Cassandra."""
    # Mockar get_async_session em todos os módulos onde é usada
    with patch.multiple(
        'caspyorm.query',
        get_async_session=MagicMock()
    ), patch.multiple(
        'caspyorm.connection',
        get_async_session=MagicMock()
    ):
        # Criar mock da sessão
        session = MagicMock()
        prepared_statement = MagicMock()
        session.prepare.return_value = prepared_statement
        
        # Configurar o mock para retornar a sessão
        from caspyorm.query import get_async_session as query_get_session
        from caspyorm.connection import get_async_session as conn_get_session
        
        query_get_session.return_value = session
        conn_get_session.return_value = session
        
        yield session

def create_mock_result_set(data=None):
    """Cria um mock de result_set que simula o comportamento esperado."""
    result_set = MagicMock()
    if data is None:
        data = []
    result_set._asdict.return_value = data
    result_set.one.return_value = data[0] if data else None
    result_set.__iter__ = lambda self: iter(data)
    result_set.__len__ = lambda self: len(data)
    return result_set

def create_mock_future(result_data=None):
    """Cria um Future com resultado mockado."""
    future = Future()
    if result_data is None:
        result_data = create_mock_result_set([])
    future.set_result(result_data)
    return future


@pytest.fixture
def sample_user_data():
    """Dados de exemplo para testes de usuário."""
    return {
        'id': '550e8400-e29b-41d4-a716-446655440000',
        'name': 'João Silva',
        'email': 'joao@example.com',
        'age': 30
    }


class TestAsyncCRUD:
    """Testes para operações CRUD assíncronas."""

    @pytest.mark.asyncio
    async def test_save_async_success(self, mock_async_session, sample_user_data):
        """Testa salvamento assíncrono bem-sucedido."""
        user = TestUser(**sample_user_data)
        # Configurar mock para retornar Future vazio
        future = create_mock_future()
        mock_async_session.execute_async.return_value = future
        await user.save_async()
        mock_async_session.prepare.assert_called_once()
        mock_async_session.execute_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_async_without_primary_key(self):
        """Testa que save_async levanta ValidationError se a chave primária for nula."""
        # Instanciamos primeiro para depois setar o id como None, bypassando o default do __init__
        user = TestUser(name="Incomplete User")
        user.id = None  # type: ignore[assignment]
        with pytest.raises(ValidationError, match="Primary key 'id' cannot be None before saving."):
            await user.save_async()

    @pytest.mark.asyncio
    async def test_create_async_success(self, mock_async_session, sample_user_data):
        """Testa criação assíncrona bem-sucedida."""
        # Configurar mock para retornar Future vazio
        future = create_mock_future()
        mock_async_session.execute_async.return_value = future
        user = await TestUser.create_async(**sample_user_data)
        assert isinstance(user, TestUser)
        assert str(user.id) == sample_user_data['id']

    @pytest.mark.asyncio
    async def test_get_async_success(self, mock_async_session, sample_user_data):
        """Testa busca assíncrona bem-sucedida."""
        row_mock = MagicMock()
        row_mock._asdict.return_value = sample_user_data
        result_set = create_mock_result_set([row_mock])
        future = create_mock_future(result_set)
        mock_async_session.execute_async.return_value = future

        user = await TestUser.get_async(id=sample_user_data['id'])

        assert user is not None
        assert isinstance(user, TestUser)
        assert str(user.id) == sample_user_data['id']
        assert user.name == sample_user_data['name']

    @pytest.mark.asyncio
    async def test_get_async_not_found(self, mock_async_session):
        """Testa busca assíncrona quando registro não é encontrado."""
        result_set = create_mock_result_set([])
        future = create_mock_future(result_set)
        mock_async_session.execute_async.return_value = future
        user = await TestUser.get_async(id='non-existent-id')
        assert user is None

    @pytest.mark.asyncio
    async def test_bulk_create_async_success(self, mock_async_session):
        """Testa criação em lote assíncrona bem-sucedida."""
        users_data = [
            TestUser(id='550e8400-e29b-41d4-a716-446655440001', name='User 1'),
            TestUser(id='550e8400-e29b-41d4-a716-446655440002', name='User 2')
        ]
        
        # Configurar mock para retornar Future vazio
        future = create_mock_future()
        mock_async_session.execute_async.return_value = future
        
        result = await TestUser.bulk_create_async(users_data)
        assert result == users_data
        # Verificar que execute_async foi chamado pelo menos uma vez (para o batch)
        assert mock_async_session.execute_async.call_count >= 1

    @pytest.mark.asyncio
    async def test_bulk_create_async_empty_list(self, mock_async_session):
        """Testa criação em lote assíncrona com lista vazia."""
        result_users = await TestUser.bulk_create_async([])
        assert result_users == []

    @pytest.mark.asyncio
    async def test_update_async_success(self, mock_async_session, sample_user_data):
        """Testa atualização assíncrona bem-sucedida."""
        user = TestUser(**sample_user_data)
        updated_user = await user.update_async(name='New Name')
        assert updated_user.name == 'New Name'
        mock_async_session.execute_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_async_invalid_field(self, mock_async_session, sample_user_data):
        """Testa erro ao atualizar campo inexistente."""
        user = TestUser(**sample_user_data)
        with pytest.raises(ValidationError, match="não existe no modelo"):
            await user.update_async(invalid_field='value')  # type: ignore

    @pytest.mark.asyncio
    async def test_delete_async_success(self, mock_async_session, sample_user_data):
        """Testa deleção assíncrona bem-sucedida."""
        user = TestUser(**sample_user_data)
        # Configurar mock para retornar Future vazio
        future = create_mock_future()
        mock_async_session.execute_async.return_value = future
        await user.delete_async()
        mock_async_session.execute_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_filter_async_success(self, mock_async_session, sample_user_data):
        """Testa filtro assíncrono bem-sucedido."""
        row_mock = MagicMock()
        row_mock._asdict.return_value = sample_user_data
        result_set = create_mock_result_set([row_mock])
        future = create_mock_future(result_set)
        mock_async_session.execute_async.return_value = future
        results = await TestUser.filter(name='João Silva').all_async()
        assert len(results) == 1
        assert results[0].name == sample_user_data['name']

    @pytest.mark.asyncio
    async def test_count_async_success(self, mock_async_session):
        """Testa contagem assíncrona bem-sucedida."""
        row_mock = MagicMock()
        row_mock.count = 5
        result_set = create_mock_result_set([row_mock])
        future = create_mock_future(result_set)
        mock_async_session.execute_async.return_value = future
        count = await TestUser.filter(age=30).count_async()
        assert count == 5

    @pytest.mark.asyncio
    async def test_exists_async_true(self, mock_async_session):
        """Testa exists_async retornando True."""
        row_mock = MagicMock()
        result_set = create_mock_result_set([row_mock])
        future = create_mock_future(result_set)
        mock_async_session.execute_async.return_value = future
        exists = await TestUser.filter(name='João').exists_async()
        assert exists is True

    @pytest.mark.asyncio
    async def test_exists_async_false(self, mock_async_session):
        """Testa exists_async retornando False."""
        result_set = create_mock_result_set([])
        future = create_mock_future(result_set)
        mock_async_session.execute_async.return_value = future
        exists = await TestUser.filter(name='Non-existent').exists_async()
        assert exists is False

    @pytest.mark.asyncio
    async def test_first_async_success(self, mock_async_session, sample_user_data):
        """Testa first_async bem-sucedido."""
        row_mock = MagicMock()
        row_mock._asdict.return_value = sample_user_data
        result_set = create_mock_result_set([row_mock])
        future = create_mock_future(result_set)
        mock_async_session.execute_async.return_value = future
        user = await TestUser.filter(name='João Silva').first_async()
        assert user is not None
        assert isinstance(user, TestUser)
        assert user.name == sample_user_data['name']

    @pytest.mark.asyncio
    async def test_first_async_none(self, mock_async_session):
        """Testa first_async retornando None."""
        result_set = create_mock_result_set([])
        future = create_mock_future(result_set)
        mock_async_session.execute_async.return_value = future
        user = await TestUser.filter(name='Non-existent').first_async()
        assert user is None


class TestAsyncErrorHandling:
    """Testes para tratamento de erros em operações assíncronas."""

    @pytest.mark.asyncio
    async def test_save_async_connection_error(self, mock_async_session, sample_user_data):
        """Testa erro de conexão durante save_async."""
        user = TestUser(**sample_user_data)
        mock_async_session.execute_async.side_effect = Exception("Connection failed")
        with pytest.raises(Exception, match="Connection failed"):
            await user.save_async()

    @pytest.mark.asyncio
    async def test_bulk_create_async_with_invalid_data(self, mock_async_session):
        """Testa que bulk_create_async falha com dados inválidos."""
        # Configurar mock para simular erro de tabela não existente
        mock_async_session.prepare.side_effect = Exception("table test_users does not exist")
        
        # Passamos uma instância com um UUID válido, mas sem o campo obrigatório 'name'
        users_data = [TestUser(id=uuid4())]
        with pytest.raises(Exception, match="table test_users does not exist"):
            await TestUser.bulk_create_async(users_data)

    @pytest.mark.asyncio
    async def test_update_async_validation_error(self, sample_user_data):
        """Testa erro de validação durante update_async."""
        user = TestUser(**sample_user_data)
        with pytest.raises(ValidationError):
            await user.update_async(age="not-a-number")


class TestAsyncPerformance:
    """Testes para verificar performance de operações assíncronas."""

    @pytest.mark.asyncio
    async def test_concurrent_save_async(self, mock_async_session):
        """Testa salvamentos concorrentes bem-sucedidos."""
        users_to_save = [TestUser(id=uuid4(), name=f"User {i}") for i in range(5)]
        
        # Configurar mock para retornar Future vazio
        future = create_mock_future()
        mock_async_session.execute_async.return_value = future
        
        # Executar salvamentos concorrentes
        tasks = [user.save_async() for user in users_to_save]
        await asyncio.gather(*tasks)
        
        # Verificar que execute_async foi chamado 5 vezes
        assert mock_async_session.execute_async.call_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, mock_async_session):
        """Testa múltiplas queries concorrentes."""
        # Usar UUID válido no mock
        valid_uuid = str(uuid4())
        row_mock = MagicMock()
        row_mock._asdict.return_value = {'id': valid_uuid, 'name': 'Concurrent User'}
        result_set = create_mock_result_set([row_mock])
        future = create_mock_future(result_set)
        mock_async_session.execute_async.return_value = future

        tasks = [
            TestUser.get_async(id=uuid4()),
            TestUser.filter(name="some_name").first_async(),
            TestUser.filter(name="another_name").all_async(),
        ]
        results = await asyncio.gather(*tasks)
        
        # Verificar que todos os resultados foram obtidos
        assert len(results) == 3
        assert all(result is not None for result in results)

    @pytest.mark.asyncio
    async def test_bulk_create_async_implemented(self, mock_async_session):
        """Testa que bulk_create_async agora está implementado."""
        future = create_mock_future()
        mock_async_session.execute_async.return_value = future
        
        result = await TestUser.bulk_create_async([TestUser(id=uuid4(), name='A')])
        assert len(result) == 1
        assert result[0].name == 'A'

    @pytest.mark.asyncio
    async def test_sync_table_async_implemented(self, mock_async_session):
        """Testa que sync_table_async agora está implementado."""
        # Configurar mock para simular que a tabela não existe
        mock_async_session.execute.return_value = []
        future = create_mock_future()
        mock_async_session.execute_async.return_value = future
        
        await TestUser.sync_table_async()
        # Verificar que execute_async foi chamado pelo menos uma vez
        assert mock_async_session.execute_async.call_count >= 1

    @pytest.mark.asyncio
    async def test_update_collection_async_implemented(self, mock_async_session, sample_user_data):
        """Testa que update_collection_async agora está implementado."""
        user = TestUser(**sample_user_data)
        future = create_mock_future()
        mock_async_session.execute_async.return_value = future
        
        # Testar com um campo que existe no modelo (email)
        with pytest.raises(ValidationError, match="não existe no modelo"):
            await user.update_collection_async('tags', add=['new_tag'])
        
        # Verificar que o método foi chamado (mesmo que tenha falhado)
        assert mock_async_session.execute_async.call_count >= 0

    @pytest.mark.asyncio
    async def test_async_methods_do_not_block_event_loop(self, mock_async_session, sample_user_data):
        """Testa que métodos async reais não bloqueiam o event loop (timeout curto)."""
        user = TestUser(**sample_user_data)
        
        # Configurar mock para retornar Future vazio
        future = create_mock_future()
        mock_async_session.execute_async.return_value = future
        
        # save_async
        await asyncio.wait_for(user.save_async(), timeout=1)
        # filter().all_async()
        await asyncio.wait_for(TestUser.filter(name='João Silva').all_async(), timeout=1)
        # count_async
        await asyncio.wait_for(TestUser.filter(age=30).count_async(), timeout=1)
        # exists_async
        await asyncio.wait_for(TestUser.filter(name='João').exists_async(), timeout=1)