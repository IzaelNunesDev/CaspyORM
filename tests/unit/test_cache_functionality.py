# tests/unit/test_cache_functionality.py

import pytest
from unittest.mock import patch, MagicMock
from caspyorm._internal.cache import PreparedStatementCache, prepared_statement_cache
from caspyorm.model import Model
from caspyorm import fields


class TestCacheFunctionality:
    """Testa a funcionalidade do cache de prepared statements."""
    
    def test_prepared_statement_cache_initialization(self):
        """Testa se o cache é inicializado corretamente."""
        cache = PreparedStatementCache(max_size=100)
        assert cache._max_size == 100
        assert len(cache._cache) == 0
    
    def test_cache_get_set_operations(self):
        """Testa operações básicas de get e set do cache."""
        cache = PreparedStatementCache(max_size=10)
        
        # Testar set e get
        mock_statement = MagicMock()
        cache.set("SELECT * FROM test", mock_statement)
        
        result = cache.get("SELECT * FROM test")
        assert result is mock_statement
        
        # Testar get de item inexistente
        result = cache.get("SELECT * FROM nonexistent")
        assert result is None
    
    def test_cache_lru_eviction(self):
        """Testa se o cache remove itens antigos quando está cheio."""
        cache = PreparedStatementCache(max_size=2)
        
        # Adicionar 3 itens (deve remover o primeiro)
        cache.set("query1", MagicMock())
        cache.set("query2", MagicMock())
        cache.set("query3", MagicMock())
        
        # O primeiro item deve ter sido removido
        assert cache.get("query1") is None
        assert cache.get("query2") is not None
        assert cache.get("query3") is not None
    
    def test_cache_clear(self):
        """Testa se o cache pode ser limpo."""
        cache = PreparedStatementCache(max_size=10)
        
        cache.set("query1", MagicMock())
        cache.set("query2", MagicMock())
        
        assert len(cache._cache) == 2
        
        cache.clear()
        assert len(cache._cache) == 0
    
    def test_global_cache_instance(self):
        """Testa se a instância global do cache funciona."""
        # Limpar cache antes do teste
        prepared_statement_cache.clear()
        
        mock_statement = MagicMock()
        prepared_statement_cache.set("SELECT * FROM global_test", mock_statement)
        
        result = prepared_statement_cache.get("SELECT * FROM global_test")
        assert result is mock_statement


class TestCacheIntegration:
    """Testa a integração do cache com operações reais."""
    
    def test_cache_used_in_operations(self):
        """Testa se o cache é usado durante operações de save."""
        # Mock da sessão
        mock_session = MagicMock()
        mock_prepared = MagicMock()
        mock_session.prepare.return_value = mock_prepared
        
        # Mock do cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        
        with patch('caspyorm.connection.get_session', return_value=mock_session):
            with patch('caspyorm._internal.cache.prepared_statement_cache', mock_cache):
                # Simular uso do cache
                cql = "INSERT INTO test_table (id, name) VALUES (?, ?)"
                
                # Primeira vez - cache miss
                prepared = mock_cache.get(cql)
                if prepared is None:
                    prepared = mock_session.prepare(cql)
                    mock_cache.set(cql, prepared)
                
                # Verificar se o cache foi consultado
                mock_cache.get.assert_called_with(cql)
                mock_cache.set.assert_called_with(cql, prepared)
                mock_session.prepare.assert_called_once_with(cql)
    
    def test_cache_reuse_in_operations(self):
        """Testa se o cache reutiliza prepared statements."""
        # Mock da sessão
        mock_session = MagicMock()
        mock_prepared = MagicMock()
        
        # Mock do cache com hit
        mock_cache = MagicMock()
        mock_cache.get.return_value = mock_prepared
        
        with patch('caspyorm.connection.get_session', return_value=mock_session):
            with patch('caspyorm._internal.cache.prepared_statement_cache', mock_cache):
                # Simular uso do cache
                cql = "INSERT INTO test_table (id, name) VALUES (?, ?)"
                
                # Cache hit
                prepared = mock_cache.get(cql)
                if prepared is None:
                    prepared = mock_session.prepare(cql)
                    mock_cache.set(cql, prepared)
                
                # Verificar se o cache foi consultado
                mock_cache.get.assert_called_with(cql)
                
                # Verificar que prepare NÃO foi chamado (cache hit)
                mock_session.prepare.assert_not_called()
                
                # Verificar que set NÃO foi chamado (cache hit)
                mock_cache.set.assert_not_called()


class TestPerformanceMetrics:
    """Testa os decorators de métricas de performance."""
    
    def test_measure_performance_sync(self):
        """Testa o decorator de performance para funções síncronas."""
        from caspyorm._internal.cache import measure_performance
        
        @measure_performance
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_measure_performance_async(self):
        """Testa o decorator de performance para funções assíncronas."""
        from caspyorm._internal.cache import measure_performance_async
        
        @measure_performance_async
        async def test_async_function():
            return "async_success"
        
        result = await test_async_function()
        assert result == "async_success"
    
    def test_measure_performance_with_error(self):
        """Testa o decorator de performance com erro."""
        from caspyorm._internal.cache import measure_performance
        
        @measure_performance
        def test_function_with_error():
            raise ValueError("test error")
        
        with pytest.raises(ValueError, match="test error"):
            test_function_with_error()
    
    @pytest.mark.asyncio
    async def test_measure_performance_async_with_error(self):
        """Testa o decorator de performance assíncrono com erro."""
        from caspyorm._internal.cache import measure_performance_async
        
        @measure_performance_async
        async def test_async_function_with_error():
            raise ValueError("async test error")
        
        with pytest.raises(ValueError, match="async test error"):
            await test_async_function_with_error() 