"""
Testes unitários para operações CRUD assíncronas da CaspyORM.
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

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
    # O patch deve ser aplicado onde o objeto original está, que é 'caspyorm.session'.
    # Qualquer módulo que importe 'get_async_session' a partir daí será mockado.
    with patch('caspyorm.session.get_async_session') as mock_get_session:
        # O mock da sessão principal não precisa ser um AsyncMock
        session = MagicMock()
        
        # .prepare() retorna um statement mockado
        prepared_statement = MagicMock()
        session.prepare.return_value = prepared_statement
        
        # .execute_async() retorna um 'future' mockado
        future = MagicMock()
        session.execute_async.return_value = future
        
        # O future.result() é o que retorna os dados mockados
        # Os testes individuais podem sobreescrever este .result()
        future.result.return_value = []
        
        session = MagicMock()
        session.prepare.return_value = prepared_statement
        session.execute_async.return_value = future
        
        mock_get_session.return_value = session
        yield session


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
        await user.save_async()
        mock_async_session.prepare.assert_called_once()
        mock_async_session.execute_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_async_without_primary_key(self):
        """Testa que save_async levanta ValidationError se a chave primária for nula."""
        # Instanciamos primeiro para depois setar o id como None, bypassando o default do __init__
        user = TestUser(name="Incomplete User")
        user.id = None 
        with pytest.raises(ValidationError, match="Primary key 'id' cannot be None before saving."):
            await user.save_async()

    @pytest.mark.asyncio
    async def test_create_async_success(self, mock_async_session, sample_user_data):
        """Testa criação assíncrona bem-sucedida."""
        user = await TestUser.create_async(**sample_user_data)
        assert isinstance(user, TestUser)
        assert str(user.id) == sample_user_data['id']

    @pytest.mark.asyncio
    async def test_get_async_success(self, mock_async_session, sample_user_data):
        """Testa busca assíncrona bem-sucedida."""
        row_mock = MagicMock()
        row_mock._asdict.return_value = sample_user_data
        # .get_async() chama .first_async(), que chama .all_async(), que itera sobre o resultado.
        # Portanto, o resultado deve ser um iterável (lista).
        mock_async_session.execute_async.return_value.result.return_value = [row_mock]

        user = await TestUser.get_async(id=sample_user_data['id'])

        assert user is not None
        assert isinstance(user, TestUser)
        assert str(user.id) == sample_user_data['id']
        assert user.name == sample_user_data['name']

    @pytest.mark.asyncio
    async def test_get_async_not_found(self, mock_async_session):
        """Testa busca assíncrona quando registro não é encontrado."""
        result_set = MagicMock()
        result_set.one.return_value = None
        mock_async_session.execute_async.return_value.result.return_value = result_set
        user = await TestUser.get_async(id='non-existent-id')
        assert user is None

    @pytest.mark.asyncio
    async def test_bulk_create_async_success(self, mock_async_session):
        """Testa criação em lote assíncrona bem-sucedida."""
        users_data = [
            TestUser(id='550e8400-e29b-41d4-a716-446655440001', name='User 1'),
            TestUser(id='550e8400-e29b-41d4-a716-446655440002', name='User 2')
        ]
        await TestUser.bulk_create_async(users_data)
        assert mock_async_session.execute_async.call_count == 2

    @pytest.mark.asyncio
    async def test_bulk_create_async_empty_list(self, mock_async_session):
        """Testa criação em lote assíncrona com lista vazia."""
        result_users = await TestUser.bulk_create_async([])
        assert result_users == []
        mock_async_session.execute_async.assert_not_called()

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
            await user.update_async(invalid_field='value')

    @pytest.mark.asyncio
    async def test_delete_async_success(self, mock_async_session, sample_user_data):
        """Testa deleção assíncrona bem-sucedida."""
        user = TestUser(**sample_user_data)
        await user.delete_async()
        mock_async_session.execute_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_filter_async_success(self, mock_async_session, sample_user_data):
        """Testa filtro assíncrono bem-sucedido."""
        row_mock = MagicMock()
        row_mock._asdict.return_value = sample_user_data
        mock_async_session.execute_async.return_value.result.return_value = [row_mock]
        results = await TestUser.filter(name='João Silva').all_async()
        assert len(results) == 1
        assert results[0].name == sample_user_data['name']

    @pytest.mark.asyncio
    async def test_count_async_success(self, mock_async_session):
        """Testa contagem assíncrona bem-sucedida."""
        row_mock = MagicMock()
        row_mock.count = 5
        result_set = MagicMock()
        result_set.one.return_value = row_mock
        mock_async_session.execute_async.return_value.result.return_value = result_set
        count = await TestUser.filter(age=30).count_async()
        assert count == 5

    @pytest.mark.asyncio
    async def test_exists_async_true(self, mock_async_session):
        """Testa exists_async retornando True."""
        row_mock = MagicMock()
        result_set = MagicMock()
        result_set.one.return_value = row_mock
        mock_async_session.execute_async.return_value.result.return_value = result_set
        exists = await TestUser.filter(name='João').exists_async()
        assert exists is True

    @pytest.mark.asyncio
    async def test_exists_async_false(self, mock_async_session):
        """Testa exists_async retornando False."""
        result_set = MagicMock()
        result_set.one.return_value = None
        mock_async_session.execute_async.return_value.result.return_value = result_set
        exists = await TestUser.filter(name='Non-existent').exists_async()
        assert exists is False

    @pytest.mark.asyncio
    async def test_first_async_success(self, mock_async_session, sample_user_data):
        """Testa first_async bem-sucedido."""
        row_mock = MagicMock()
        row_mock._asdict.return_value = sample_user_data
        mock_async_session.execute_async.return_value.result.return_value = [row_mock]
        user = await TestUser.filter(name='João').first_async()
        assert user is not None
        assert user.name == sample_user_data['name']

    @pytest.mark.asyncio
    async def test_first_async_none(self, mock_async_session):
        """Testa first_async retornando None."""
        mock_async_session.execute_async.return_value.result.return_value = []
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
    async def test_bulk_create_async_with_invalid_data(self):
        """Testa que bulk_create_async falha com dados inválidos."""
        # Passamos uma instância com um UUID válido, mas sem o campo obrigatório 'name'
        users_data = [TestUser(id=uuid4())]
        with pytest.raises(ValidationError):
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

        mock_async_session.execute_async.return_value.result.return_value = []

        tasks = [user.save_async() for user in users_to_save]
        results = await asyncio.gather(*tasks)

        assert mock_async_session.prepare.call_count == 5
        assert mock_async_session.execute_async.call_count == 5
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, mock_async_session):
        """Testa múltiplas queries concorrentes."""
        row_mock = MagicMock()
        row_mock._asdict.return_value = {'id': 'test-id', 'name': 'Concurrent User'}

        # Para cada chamada, um novo future com um resultado iterável é retornado
        def result_side_effect(*args, **kwargs):
            future = MagicMock()
            future.result.return_value = [row_mock]
            return future

        mock_async_session.execute_async.side_effect = result_side_effect

        tasks = [
            TestUser.get_async(id=uuid4()),
            TestUser.filter(name="some_name").first_async(),
            TestUser.filter(name="another_name").all_async(),
        ]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert mock_async_session.execute_async.call_count == 3
        assert isinstance(results[0], TestUser)
        assert isinstance(results[1], TestUser)
        assert isinstance(results[2], list)