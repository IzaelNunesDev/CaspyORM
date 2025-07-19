"""
Testes para sincronização de schema.

Este módulo testa todas as funcionalidades do módulo _internal/schema_sync.py
para garantir que a sincronização de schema funciona corretamente.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from caspyorm._internal.schema_sync import (
    _get_cql_type,
    get_cassandra_table_schema,
    apply_schema_changes,
    build_create_table_cql,
    build_create_index_cql,
    get_existing_indexes,
    create_indexes_for_table,
    sync_table,
    sync_table_async,
    apply_schema_changes_async,
    create_indexes_for_table_async,
    get_async_session
)
from caspyorm.exceptions import ValidationError, ObjectNotFound, MultipleObjectsReturned, ConnectionError
from caspyorm.model import Model
from caspyorm.fields import Text, Integer, UUID

# Modelo de teste para os testes
class TestUser(Model):
    """Modelo de teste para os testes de schema."""
    __table_name__ = "test_users"
    
    id = UUID(primary_key=True)
    name = Text()
    age = Integer()
    email = Text(index=True)


class TestSchemaSync:
    """Testes para as funções de sincronização de schema."""
    
    def test_get_cql_type_basic_types(self):
        """Testa _get_cql_type com tipos básicos."""
        assert _get_cql_type('text') == 'text'
        assert _get_cql_type('int') == 'int'
        assert _get_cql_type('uuid') == 'uuid'
        assert _get_cql_type('boolean') == 'boolean'
        assert _get_cql_type('timestamp') == 'timestamp'
    
    def test_get_cql_type_complex_types(self):
        """Testa _get_cql_type com tipos complexos."""
        assert _get_cql_type('list<text>') == 'list<text>'
        assert _get_cql_type('map<text, int>') == 'map<text, text>'
        assert _get_cql_type('set<uuid>') == 'set<text>'
    
    def test_get_cql_type_unknown_type(self):
        """Testa _get_cql_type com tipo desconhecido."""
        assert _get_cql_type('unknown_type') == 'text'
    
    def test_get_cassandra_table_schema_success(self):
        """Testa get_cassandra_table_schema com sucesso."""
        mock_session = Mock()
        mock_row1 = Mock()
        mock_row1.column_name = 'id'
        mock_row1.type = 'uuid'
        mock_row1.kind = 'partition_key'
        
        mock_row2 = Mock()
        mock_row2.column_name = 'name'
        mock_row2.type = 'text'
        mock_row2.kind = 'regular'
        
        mock_session.execute.return_value = [mock_row1, mock_row2]
        
        schema = get_cassandra_table_schema(mock_session, 'test_keyspace', 'test_table')
        
        assert schema is not None
        assert 'id' in schema['fields']
        assert 'name' in schema['fields']
        assert schema['fields']['id']['type'] == 'uuid'
        assert schema['fields']['name']['type'] == 'text'
        assert 'id' in schema['partition_keys']
        assert 'id' in schema['primary_keys']
    
    def test_get_cassandra_table_schema_table_not_exists(self):
        """Testa get_cassandra_table_schema quando a tabela não existe."""
        mock_session = Mock()
        mock_session.execute.return_value = []
        
        schema = get_cassandra_table_schema(mock_session, 'test_keyspace', 'test_table')
        
        assert schema is None
    
    def test_get_cassandra_table_schema_exception(self):
        """Testa get_cassandra_table_schema com exceção."""
        mock_session = Mock()
        mock_session.execute.side_effect = Exception("Database error")
        
        schema = get_cassandra_table_schema(mock_session, 'test_keyspace', 'test_table')
        
        assert schema is None
    
    def test_build_create_table_cql_simple_primary_key(self):
        """Testa build_create_table_cql com chave primária simples."""
        schema = {
            'fields': {
                'id': {'type': 'uuid'},
                'name': {'type': 'text'},
                'age': {'type': 'int'}
            },
            'partition_keys': ['id'],
            'clustering_keys': []
        }
    
        cql = build_create_table_cql('test_table', schema)
    
        assert 'CREATE TABLE IF NOT EXISTS test_table' in cql
        assert 'id uuid' in cql
        assert 'name text' in cql
        assert 'age int' in cql
        assert 'PRIMARY KEY (id)' in cql
    
    def test_build_create_table_cql_composite_primary_key(self):
        """Testa build_create_table_cql com chave primária composta."""
        schema = {
            'fields': {
                'id': {'type': 'uuid'},
                'name': {'type': 'text'},
                'age': {'type': 'int'},
                'email': {'type': 'text'}
            },
            'partition_keys': ['id'],
            'clustering_keys': ['email']
        }
    
        cql = build_create_table_cql('test_table', schema)
    
        assert 'CREATE TABLE IF NOT EXISTS test_table' in cql
        assert 'id uuid' in cql
        assert 'name text' in cql
        assert 'age int' in cql
        assert 'email text' in cql
        assert 'PRIMARY KEY (id, email)' in cql
    
    def test_build_create_table_cql_multiple_partition_keys(self):
        """Testa build_create_table_cql com múltiplas chaves de partição."""
        schema = {
            'fields': {
                'id': {'type': 'uuid'},
                'tenant_id': {'type': 'uuid'},
                'name': {'type': 'text'}
            },
            'partition_keys': ['id', 'tenant_id'],
            'clustering_keys': []
        }
    
        cql = build_create_table_cql('test_table', schema)
    
        assert 'CREATE TABLE IF NOT EXISTS test_table' in cql
        assert 'id uuid' in cql
        assert 'tenant_id uuid' in cql
        assert 'name text' in cql
        assert 'PRIMARY KEY ((id, tenant_id))' in cql
    
    def test_build_create_table_cql_no_primary_key(self):
        """Testa build_create_table_cql sem chave primária."""
        schema = {
            'fields': {
                'name': {'type': 'text'},
                'age': {'type': 'int'}
            },
            'partition_keys': [],
            'clustering_keys': []
        }
    
        with pytest.raises(RuntimeError, match="Tabela deve ter pelo menos uma chave primária"):
            build_create_table_cql('test_table', schema)
    
    def test_build_create_index_cql(self):
        """Testa build_create_index_cql."""
        cql = build_create_index_cql('test_table', 'name')
        
        assert 'CREATE INDEX IF NOT EXISTS test_table_name_idx' in cql
        assert 'ON test_table (name)' in cql
    
    def test_get_existing_indexes_success(self):
        """Testa get_existing_indexes com sucesso."""
        mock_session = Mock()
        mock_row1 = Mock()
        mock_row1.index_name = 'test_table_name_idx'
        mock_row2 = Mock()
        mock_row2.index_name = 'test_table_email_idx'
        
        mock_session.execute.return_value = [mock_row1, mock_row2]
        
        indexes = get_existing_indexes(mock_session, 'test_keyspace', 'test_table')
        
        assert 'test_table_name_idx' in indexes
        assert 'test_table_email_idx' in indexes
    
    def test_get_existing_indexes_no_indexes(self):
        """Testa get_existing_indexes quando não há índices."""
        mock_session = Mock()
        mock_session.execute.return_value = []
        
        indexes = get_existing_indexes(mock_session, 'test_keyspace', 'test_table')
        
        assert indexes == set()
    
    def test_create_indexes_for_table_success(self):
        """Testa create_indexes_for_table com sucesso."""
        mock_session = Mock()
        mock_session.keyspace = 'test_keyspace'
        mock_session.execute.return_value = []
        
        model_schema = {
            'fields': {
                'id': {'type': 'uuid'},
                'name': {'type': 'text', 'index': True},
                'email': {'type': 'text', 'index': True}
            }
        }
        
        with patch('caspyorm._internal.schema_sync.get_existing_indexes', return_value=set()):
            create_indexes_for_table(mock_session, 'test_table', model_schema, verbose=False)
        
        # Verifica se execute foi chamado para cada índice
        assert mock_session.execute.call_count == 2
    
    def test_create_indexes_for_table_no_indexes(self):
        """Testa create_indexes_for_table sem índices."""
        mock_session = Mock()
        
        model_schema = {
            'fields': {
                'id': {'type': 'uuid'},
                'name': {'type': 'text'},
                'email': {'type': 'text'}
            }
        }
        
        create_indexes_for_table(mock_session, 'test_table', model_schema, verbose=False)
        
        # Não deve chamar execute
        mock_session.execute.assert_not_called()
    
    def test_sync_table_table_exists_no_changes(self):
        """Testa sync_table quando a tabela existe e não há mudanças."""
        mock_session = Mock()
        mock_session.keyspace = 'test_keyspace'
        
        # Mock do schema do banco
        db_schema = {
            'fields': {
                'id': {'type': 'uuid', 'kind': 'partition_key'},
                'name': {'type': 'text', 'kind': 'regular'},
                'age': {'type': 'int', 'kind': 'regular'}
            },
            'partition_keys': ['id'],
            'clustering_keys': [],
            'primary_keys': ['id']
        }
        
        with patch('caspyorm._internal.schema_sync.get_cassandra_table_schema', return_value=db_schema), \
             patch('caspyorm._internal.schema_sync.get_session', return_value=mock_session):
            
            sync_table(TestUser, auto_apply=False, verbose=False)
    
    def test_sync_table_table_exists_with_new_column(self):
        """Testa sync_table quando há uma nova coluna."""
        mock_session = Mock()
        mock_session.keyspace = 'test_keyspace'
        
        # Mock do schema do banco (sem email)
        db_schema = {
            'fields': {
                'id': {'type': 'uuid', 'kind': 'partition_key'},
                'name': {'type': 'text', 'kind': 'regular'},
                'age': {'type': 'int', 'kind': 'regular'}
            },
            'partition_keys': ['id'],
            'clustering_keys': [],
            'primary_keys': ['id']
        }
        
        with patch('caspyorm._internal.schema_sync.get_cassandra_table_schema', return_value=db_schema), \
             patch('caspyorm._internal.schema_sync.get_session', return_value=mock_session):
            
            sync_table(TestUser, auto_apply=True, verbose=False)
            
            # Verifica se execute foi chamado para adicionar a coluna
            assert mock_session.execute.call_count >= 1
    
    def test_sync_table_table_not_exists(self):
        """Testa sync_table quando a tabela não existe."""
        mock_session = Mock()
        mock_session.keyspace = 'test_keyspace'
        
        with patch('caspyorm._internal.schema_sync.get_cassandra_table_schema', return_value=None), \
             patch('caspyorm._internal.schema_sync.get_session', return_value=mock_session):
            
            sync_table(TestUser, auto_apply=True, verbose=False)
            
            # Verifica se execute foi chamado para criar a tabela
            assert mock_session.execute.call_count >= 1
    
    def test_sync_table_primary_key_change(self):
        """Testa sync_table quando há mudança na chave primária."""
        mock_session = Mock()
        mock_session.keyspace = 'test_keyspace'
        
        # Mock do schema do banco com chave primária diferente
        db_schema = {
            'fields': {
                'id': {'type': 'uuid', 'kind': 'partition_key'},
                'name': {'type': 'text', 'kind': 'partition_key'},  # name como partition key
                'age': {'type': 'int', 'kind': 'regular'}
            },
            'partition_keys': ['id', 'name'],
            'clustering_keys': [],
            'primary_keys': ['id', 'name']
        }
        
        with patch('caspyorm._internal.schema_sync.get_cassandra_table_schema', return_value=db_schema), \
             patch('caspyorm._internal.schema_sync.get_session', return_value=mock_session):
            
            with pytest.raises(RuntimeError, match="A alteração de chave primária não é possível"):
                sync_table(TestUser, auto_apply=True, verbose=False)
    
    def test_apply_schema_changes_add_columns(self):
        """Testa apply_schema_changes para adicionar colunas."""
        mock_session = Mock()
        
        model_schema = {
            'fields': {
                'id': {'type': 'uuid'},
                'name': {'type': 'text'},
                'email': {'type': 'text'}  # Nova coluna
            },
            'primary_keys': ['id']
        }
        
        db_schema = {
            'fields': {
                'id': {'type': 'uuid'},
                'name': {'type': 'text'}
            },
            'primary_keys': ['id']
        }
        
        apply_schema_changes(mock_session, 'test_table', model_schema, db_schema)
        
        # Verifica se execute foi chamado para adicionar a coluna
        assert mock_session.execute.call_count == 1
    
    def test_apply_schema_changes_remove_columns(self):
        """Testa apply_schema_changes para remover colunas (apenas aviso)."""
        mock_session = Mock()
        
        model_schema = {
            'fields': {
                'id': {'type': 'uuid'},
                'name': {'type': 'text'}
            },
            'primary_keys': ['id']
        }
        
        db_schema = {
            'fields': {
                'id': {'type': 'uuid'},
                'name': {'type': 'text'},
                'old_column': {'type': 'text'}  # Coluna a ser removida
            },
            'primary_keys': ['id']
        }
        
        apply_schema_changes(mock_session, 'test_table', model_schema, db_schema)
        
        # Não deve chamar execute para remover colunas
        mock_session.execute.assert_not_called()
    
    def test_apply_schema_changes_type_change(self):
        """Testa apply_schema_changes para mudança de tipo (apenas aviso)."""
        mock_session = Mock()
        
        model_schema = {
            'fields': {
                'id': {'type': 'uuid'},
                'name': {'type': 'text'},
                'age': {'type': 'bigint'}  # Mudança de tipo
            },
            'primary_keys': ['id']
        }
        
        db_schema = {
            'fields': {
                'id': {'type': 'uuid'},
                'name': {'type': 'text'},
                'age': {'type': 'int'}  # Tipo antigo
            },
            'primary_keys': ['id']
        }
        
        apply_schema_changes(mock_session, 'test_table', model_schema, db_schema)
        
        # Não deve chamar execute para mudanças de tipo
        mock_session.execute.assert_not_called()


class TestSchemaSyncAsync:
    """Testes para as funções assíncronas de sincronização de schema."""
    
    @pytest.mark.asyncio
    async def test_sync_table_async_table_exists_no_changes(self):
        """Testa sync_table_async quando a tabela existe e não há mudanças."""
        mock_session = Mock()
        mock_session.keyspace = 'test_keyspace'
        
        # Mock do schema do banco
        db_schema = {
            'fields': {
                'id': {'type': 'uuid', 'kind': 'partition_key'},
                'name': {'type': 'text', 'kind': 'regular'},
                'age': {'type': 'int', 'kind': 'regular'}
            },
            'partition_keys': ['id'],
            'clustering_keys': [],
            'primary_keys': ['id']
        }
        
        with patch('caspyorm._internal.schema_sync.get_cassandra_table_schema', return_value=db_schema), \
             patch('caspyorm._internal.schema_sync.get_async_session', return_value=mock_session):
            
            await sync_table_async(TestUser, auto_apply=False, verbose=False)
    
    @pytest.mark.asyncio
    async def test_sync_table_async_table_not_exists(self):
        """Testa sync_table_async quando a tabela não existe."""
        mock_session = Mock()
        mock_session.keyspace = 'test_keyspace'
        mock_future = Mock()
        mock_session.execute_async.return_value = mock_future
        
        with patch('caspyorm._internal.schema_sync.get_cassandra_table_schema', return_value=None), \
             patch('caspyorm._internal.schema_sync.get_async_session', return_value=mock_session), \
             patch('caspyorm._internal.schema_sync._wait_for_cassandra_future') as mock_wait:
            
            await sync_table_async(TestUser, auto_apply=True, verbose=False)
            
            # Verifica se execute_async foi chamado para criar a tabela
            assert mock_session.execute_async.call_count >= 1
            assert mock_wait.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_apply_schema_changes_async_add_columns(self):
        """Testa apply_schema_changes_async para adicionar colunas."""
        mock_session = Mock()
        mock_future = Mock()
        mock_session.execute_async.return_value = mock_future
        
        model_schema = {
            'fields': {
                'id': {'type': 'uuid'},
                'name': {'type': 'text'},
                'email': {'type': 'text'}  # Nova coluna
            },
            'primary_keys': ['id']
        }
        
        db_schema = {
            'fields': {
                'id': {'type': 'uuid'},
                'name': {'type': 'text'}
            },
            'primary_keys': ['id']
        }
        
        with patch('caspyorm._internal.schema_sync._wait_for_cassandra_future') as mock_wait:
            await apply_schema_changes_async(mock_session, 'test_table', model_schema, db_schema)
            
            # Verifica se execute_async foi chamado para adicionar a coluna
            assert mock_session.execute_async.call_count == 1
            assert mock_wait.call_count == 1
    
    @pytest.mark.asyncio
    async def test_create_indexes_for_table_async_success(self):
        """Testa create_indexes_for_table_async com sucesso."""
        mock_session = Mock()
        mock_session.keyspace = 'test_keyspace'
        mock_future = Mock()
        mock_session.execute_async.return_value = mock_future
        
        model_schema = {
            'fields': {
                'id': {'type': 'uuid'},
                'name': {'type': 'text', 'index': True},
                'email': {'type': 'text', 'index': True}
            }
        }
        
        with patch('caspyorm._internal.schema_sync.get_existing_indexes', return_value=set()), \
             patch('caspyorm._internal.schema_sync._wait_for_cassandra_future') as mock_wait:
            
            await create_indexes_for_table_async(mock_session, 'test_table', model_schema, verbose=False)
            
            # Verifica se execute_async foi chamado para cada índice
            assert mock_session.execute_async.call_count == 2
            assert mock_wait.call_count == 2
    
    @pytest.mark.asyncio
    async def test_create_indexes_for_table_async_no_indexes(self):
        """Testa create_indexes_for_table_async sem índices."""
        mock_session = Mock()
        
        model_schema = {
            'fields': {
                'id': {'type': 'uuid'},
                'name': {'type': 'text'},
                'email': {'type': 'text'}
            }
        }
        
        await create_indexes_for_table_async(mock_session, 'test_table', model_schema, verbose=False)
        
        # Não deve chamar execute_async
        mock_session.execute_async.assert_not_called()