"""
Testes unitários para operações CRUD assíncronas da CaspyORM.
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock

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
    with patch('caspyorm.query.get_async_session') as mock_get_session:
        session = AsyncMock()
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
        
        # Mock do prepare e execute_async
        prepared = MagicMock()
        mock_async_session.prepare.return_value = prepared
        
        result_mock = MagicMock()
        mock_async_session.execute_async.return_value = result_mock
        
        # Executar save_async
        await user.save_async()
        
        # Verificar se a sessão foi preparada e executada
        mock_async_session.prepare.assert_called_once()
        mock_async_session.execute_async.assert_called_once()
        result_mock.result.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_async_without_primary_key(self, mock_async_session):
        """Testa erro ao salvar sem chave primária."""
        user = TestUser(name='João', email='joao@example.com')
        
        with pytest.raises(ValidationError, match="Primary key 'id' cannot be None"):
            await user.save_async()

    @pytest.mark.asyncio
    async def test_create_async_success(self, mock_async_session, sample_user_data):
        """Testa criação assíncrona bem-sucedida."""
        # Mock do prepare e execute_async
        prepared = MagicMock()
        mock_async_session.prepare.return_value = prepared
        
        result_mock = MagicMock()
        mock_async_session.execute_async.return_value = result_mock
        
        # Executar create_async
        user = await TestUser.create_async(**sample_user_data)
        
        # Verificar se é uma instância válida
        assert isinstance(user, TestUser)
        assert user.id == sample_user_data['id']
        assert user.name == sample_user_data['name']
        assert user.email == sample_user_data['email']
        assert user.age == sample_user_data['age']
        
        # Verificar se save_async foi chamado
        mock_async_session.prepare.assert_called_once()
        mock_async_session.execute_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_async_success(self, mock_async_session, sample_user_data):
        """Testa busca assíncrona bem-sucedida."""
        # Mock do resultado da query
        row_mock = MagicMock()
        row_mock._asdict.return_value = sample_user_data
        
        result_set_mock = MagicMock()
        result_set_mock.__iter__.return_value = [row_mock]
        result_set_mock.one.return_value = row_mock
        
        prepared = MagicMock()
        mock_async_session.prepare.return_value = prepared
        
        result_mock = MagicMock()
        result_mock.result.return_value = result_set_mock
        mock_async_session.execute_async.return_value = result_mock
        
        # Executar get_async
        user = await TestUser.get_async(id=sample_user_data['id'])
        
        # Verificar resultado
        assert user is not None
        assert isinstance(user, TestUser)
        assert user.id == sample_user_data['id']
        assert user.name == sample_user_data['name']

    @pytest.mark.asyncio
    async def test_get_async_not_found(self, mock_async_session):
        """Testa busca assíncrona quando registro não é encontrado."""
        # Mock do resultado vazio
        result_set_mock = MagicMock()
        result_set_mock.__iter__.return_value = []
        result_set_mock.one.side_effect = Exception("No rows returned")
        
        prepared = MagicMock()
        mock_async_session.prepare.return_value = prepared
        
        result_mock = MagicMock()
        result_mock.result.return_value = result_set_mock
        mock_async_session.execute_async.return_value = result_mock
        
        # Executar get_async
        user = await TestUser.get_async(id='non-existent-id')
        
        # Verificar que retorna None
        assert user is None

    @pytest.mark.asyncio
    async def test_bulk_create_async_success(self, mock_async_session):
        """Testa criação em lote assíncrona bem-sucedida."""
        users_data = [
            {
                'id': '550e8400-e29b-41d4-a716-446655440001',
                'name': 'João Silva',
                'email': 'joao@example.com',
                'age': 30
            },
            {
                'id': '550e8400-e29b-41d4-a716-446655440002',
                'name': 'Maria Santos',
                'email': 'maria@example.com',
                'age': 25
            }
        ]
        
        users = [TestUser(**data) for data in users_data]
        
        # Mock do prepare e execute_async
        prepared = MagicMock()
        mock_async_session.prepare.return_value = prepared
        
        result_mock = MagicMock()
        mock_async_session.execute_async.return_value = result_mock
        
        # Executar bulk_create_async
        result_users = await TestUser.bulk_create_async(users)
        
        # Verificar resultado
        assert len(result_users) == 2
        assert all(isinstance(user, TestUser) for user in result_users)
        assert result_users[0].name == 'João Silva'
        assert result_users[1].name == 'Maria Santos'
        
        # Verificar se execute_async foi chamado
        mock_async_session.execute_async.assert_called()

    @pytest.mark.asyncio
    async def test_bulk_create_async_empty_list(self, mock_async_session):
        """Testa criação em lote assíncrona com lista vazia."""
        result_users = await TestUser.bulk_create_async([])
        
        # Verificar que retorna lista vazia
        assert result_users == []
        
        # Verificar que não foi feita nenhuma chamada ao banco
        mock_async_session.prepare.assert_not_called()
        mock_async_session.execute_async.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_async_success(self, mock_async_session, sample_user_data):
        """Testa atualização assíncrona bem-sucedida."""
        user = TestUser(**sample_user_data)
        
        # Mock do prepare e execute_async
        prepared = MagicMock()
        mock_async_session.prepare.return_value = prepared
        
        result_mock = MagicMock()
        mock_async_session.execute_async.return_value = result_mock
        
        # Executar update_async
        updated_user = await user.update_async(name='João Silva Atualizado', age=31)
        
        # Verificar que a instância foi atualizada
        assert updated_user.name == 'João Silva Atualizado'
        assert updated_user.age == 31
        assert updated_user.email == sample_user_data['email']  # Não alterado
        
        # Verificar se execute_async foi chamado
        mock_async_session.execute_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_async_invalid_field(self, mock_async_session, sample_user_data):
        """Testa erro ao atualizar campo inexistente."""
        user = TestUser(**sample_user_data)
        
        with pytest.raises(ValidationError, match="Campo 'invalid_field' não existe"):
            await user.update_async(invalid_field='value')

    @pytest.mark.asyncio
    async def test_delete_async_success(self, mock_async_session, sample_user_data):
        """Testa deleção assíncrona bem-sucedida."""
        user = TestUser(**sample_user_data)
        
        # Mock do prepare e execute_async
        prepared = MagicMock()
        mock_async_session.prepare.return_value = prepared
        
        result_mock = MagicMock()
        mock_async_session.execute_async.return_value = result_mock
        
        # Executar delete_async
        await user.delete_async()
        
        # Verificar se execute_async foi chamado
        mock_async_session.execute_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_filter_async_success(self, mock_async_session, sample_user_data):
        """Testa filtro assíncrono bem-sucedido."""
        # Mock do resultado da query
        row_mock = MagicMock()
        row_mock._asdict.return_value = sample_user_data
        
        result_set_mock = MagicMock()
        result_set_mock.__iter__.return_value = [row_mock]
        
        prepared = MagicMock()
        mock_async_session.prepare.return_value = prepared
        
        result_mock = MagicMock()
        result_mock.result.return_value = result_set_mock
        mock_async_session.execute_async.return_value = result_mock
        
        # Executar filter com all_async
        queryset = TestUser.filter(name='João Silva')
        results = await queryset.all_async()
        
        # Verificar resultado
        assert len(results) == 1
        assert isinstance(results[0], TestUser)
        assert results[0].name == 'João Silva'
        
        # Verificar se execute_async foi chamado
        mock_async_session.execute_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_async_success(self, mock_async_session):
        """Testa contagem assíncrona bem-sucedida."""
        # Mock do resultado da query COUNT
        row_mock = MagicMock()
        row_mock.count = 5
        
        result_set_mock = MagicMock()
        result_set_mock.one.return_value = row_mock
        
        prepared = MagicMock()
        mock_async_session.prepare.return_value = prepared
        
        result_mock = MagicMock()
        result_mock.result.return_value = result_set_mock
        mock_async_session.execute_async.return_value = result_mock
        
        # Executar count_async
        queryset = TestUser.filter(age=30)
        count = await queryset.count_async()
        
        # Verificar resultado
        assert count == 5
        
        # Verificar se execute_async foi chamado
        mock_async_session.execute_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_exists_async_true(self, mock_async_session):
        """Testa exists_async retornando True."""
        # Mock do resultado da query
        row_mock = MagicMock()
        row_mock._asdict.return_value = {'id': 'test-id'}
        
        result_set_mock = MagicMock()
        result_set_mock.__iter__.return_value = [row_mock]
        
        prepared = MagicMock()
        mock_async_session.prepare.return_value = prepared
        
        result_mock = MagicMock()
        result_mock.result.return_value = result_set_mock
        mock_async_session.execute_async.return_value = result_mock
        
        # Executar exists_async
        queryset = TestUser.filter(name='João')
        exists = await queryset.exists_async()
        
        # Verificar resultado
        assert exists is True

    @pytest.mark.asyncio
    async def test_exists_async_false(self, mock_async_session):
        """Testa exists_async retornando False."""
        # Mock do resultado vazio
        result_set_mock = MagicMock()
        result_set_mock.__iter__.return_value = []
        
        prepared = MagicMock()
        mock_async_session.prepare.return_value = prepared
        
        result_mock = MagicMock()
        result_mock.result.return_value = result_set_mock
        mock_async_session.execute_async.return_value = result_mock
        
        # Executar exists_async
        queryset = TestUser.filter(name='Non-existent')
        exists = await queryset.exists_async()
        
        # Verificar resultado
        assert exists is False

    @pytest.mark.asyncio
    async def test_first_async_success(self, mock_async_session, sample_user_data):
        """Testa first_async bem-sucedido."""
        # Mock do resultado da query
        row_mock = MagicMock()
        row_mock._asdict.return_value = sample_user_data
        
        result_set_mock = MagicMock()
        result_set_mock.__iter__.return_value = [row_mock]
        
        prepared = MagicMock()
        mock_async_session.prepare.return_value = prepared
        
        result_mock = MagicMock()
        result_mock.result.return_value = result_set_mock
        mock_async_session.execute_async.return_value = result_mock
        
        # Executar first_async
        queryset = TestUser.filter(name='João')
        user = await queryset.first_async()
        
        # Verificar resultado
        assert user is not None
        assert isinstance(user, TestUser)
        assert user.name == 'João Silva'

    @pytest.mark.asyncio
    async def test_first_async_none(self, mock_async_session):
        """Testa first_async retornando None."""
        # Mock do resultado vazio
        result_set_mock = MagicMock()
        result_set_mock.__iter__.return_value = []
        
        prepared = MagicMock()
        mock_async_session.prepare.return_value = prepared
        
        result_mock = MagicMock()
        result_mock.result.return_value = result_set_mock
        mock_async_session.execute_async.return_value = result_mock
        
        # Executar first_async
        queryset = TestUser.filter(name='Non-existent')
        user = await queryset.first_async()
        
        # Verificar resultado
        assert user is None


class TestAsyncErrorHandling:
    """Testes para tratamento de erros em operações assíncronas."""

    @pytest.mark.asyncio
    async def test_save_async_connection_error(self, mock_async_session, sample_user_data):
        """Testa erro de conexão durante save_async."""
        user = TestUser(**sample_user_data)
        
        # Mock do erro de conexão
        mock_async_session.prepare.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception, match="Connection failed"):
            await user.save_async()

    @pytest.mark.asyncio
    async def test_bulk_create_async_with_invalid_data(self, mock_async_session):
        """Testa erro durante bulk_create_async com dados inválidos."""
        users = [
            TestUser(id='valid-id', name='João', email='joao@example.com'),
            TestUser(name='Maria', email='maria@example.com')  # Sem ID
        ]
        
        with pytest.raises(ValueError, match="Primary key 'id' não pode ser nula"):
            await TestUser.bulk_create_async(users)

    @pytest.mark.asyncio
    async def test_update_async_validation_error(self, mock_async_session, sample_user_data):
        """Testa erro de validação durante update_async."""
        user = TestUser(**sample_user_data)
        
        # Tentar atualizar com valor inválido para campo IntField
        with pytest.raises(ValidationError):
            await user.update_async(age="not_a_number")


class TestAsyncPerformance:
    """Testes para verificar performance de operações assíncronas."""

    @pytest.mark.asyncio
    async def test_concurrent_save_async(self, mock_async_session):
        """Testa salvamento concorrente de múltiplas instâncias."""
        users = [
            TestUser(
                id=f'user-{i}',
                name=f'User {i}',
                email=f'user{i}@example.com'
            )
            for i in range(5)
        ]
        
        # Mock do prepare e execute_async
        prepared = MagicMock()
        mock_async_session.prepare.return_value = prepared
        
        result_mock = MagicMock()
        mock_async_session.execute_async.return_value = result_mock
        
        # Executar saves concorrentes
        tasks = [user.save_async() for user in users]
        await asyncio.gather(*tasks)
        
        # Verificar que execute_async foi chamado 5 vezes
        assert mock_async_session.execute_async.call_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, mock_async_session):
        """Testa execução concorrente de queries."""
        # Mock do resultado
        row_mock = MagicMock()
        row_mock._asdict.return_value = {'id': 'test', 'name': 'Test'}
        
        result_set_mock = MagicMock()
        result_set_mock.__iter__.return_value = [row_mock]
        
        prepared = MagicMock()
        mock_async_session.prepare.return_value = prepared
        
        result_mock = MagicMock()
        result_mock.result.return_value = result_set_mock
        mock_async_session.execute_async.return_value = result_mock
        
        # Executar queries concorrentes
        tasks = [
            TestUser.filter(name=f'User {i}').all_async()
            for i in range(3)
        ]
        results = await asyncio.gather(*tasks)
        
        # Verificar que todas as queries foram executadas
        assert len(results) == 3
        assert all(len(result) == 1 for result in results)
        assert mock_async_session.execute_async.call_count == 3 