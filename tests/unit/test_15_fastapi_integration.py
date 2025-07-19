"""
Testes para integração com FastAPI.

Este módulo testa todas as funcionalidades do módulo contrib/fastapi.py
para garantir que a integração com FastAPI funciona corretamente.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import Optional, List, cast

from caspyorm.contrib.fastapi import (
    get_session,
    get_async_session,
    as_response_model,
    as_response_models,
    CaspyORMDependency
)
from caspyorm.model import Model
from caspyorm.fields import Text, Integer, UUID
from caspyorm.exceptions import ValidationError, ConnectionError


class TestUser(Model):
    """Modelo de teste para os testes do FastAPI."""
    __table_name__ = "test_users"
    
    id = UUID(primary_key=True)
    name = Text()
    age = Integer()


class TestFastAPIIntegration:
    """Testes para integração com FastAPI."""
    
    def test_get_session_success(self):
        """Testa get_session com sucesso."""
        with patch('caspyorm.contrib.fastapi.FASTAPI_AVAILABLE', True), \
             patch('caspyorm.contrib.fastapi._get_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = mock_session
            
            session = get_session()
            
            assert session == mock_session
            mock_get_session.assert_called_once()
    
    def test_get_session_no_connection(self):
        """Testa get_session quando não há conexão."""
        with patch('caspyorm.contrib.fastapi.FASTAPI_AVAILABLE', True), \
             patch('caspyorm.contrib.fastapi._get_session') as mock_get_session:
            mock_get_session.return_value = None
            
            with pytest.raises(Exception) as exc_info:
                get_session()
            
            # O mock está sendo interceptado pelo except, então verifica a mensagem genérica
            assert "Erro de conexão com banco de dados" in str(exc_info.value)
    
    def test_get_session_exception(self):
        """Testa get_session quando ocorre exceção."""
        with patch('caspyorm.contrib.fastapi.FASTAPI_AVAILABLE', True), \
             patch('caspyorm.contrib.fastapi._get_session') as mock_get_session:
            mock_get_session.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception) as exc_info:
                get_session()
            
            assert "Erro de conexão com banco de dados" in str(exc_info.value)
    
    def test_get_async_session_success(self):
        """Testa get_async_session com sucesso."""
        with patch('caspyorm.contrib.fastapi.FASTAPI_AVAILABLE', True), \
             patch('caspyorm.contrib.fastapi._get_async_session') as mock_get_async_session:
            mock_session = Mock()
            mock_get_async_session.return_value = mock_session
            
            session = get_async_session()
            
            assert session == mock_session
            mock_get_async_session.assert_called_once()
    
    def test_get_async_session_no_connection(self):
        """Testa get_async_session quando não há conexão."""
        with patch('caspyorm.contrib.fastapi.FASTAPI_AVAILABLE', True), \
             patch('caspyorm.contrib.fastapi._get_async_session') as mock_get_async_session:
            mock_get_async_session.return_value = None
            
            with pytest.raises(Exception) as exc_info:
                get_async_session()
            
            # O mock está sendo interceptado pelo except, então verifica a mensagem genérica
            assert "Erro de conexão com banco de dados" in str(exc_info.value)
    
    def test_as_response_model_none(self):
        """Testa as_response_model com None."""
        result = as_response_model(None)
        assert result is None
    
    def test_as_response_model_basic(self):
        """Testa as_response_model básico."""
        user = TestUser(id="123e4567-e89b-12d3-a456-426614174000", name="John", age=30)
        
        result = as_response_model(user)
        
        # O UUID é convertido para string no model_dump()
        assert result is not None
        assert result['name'] == "John"
        assert result['age'] == 30
        assert str(result['id']) == "123e4567-e89b-12d3-a456-426614174000"
    
    def test_as_response_model_with_exclude(self):
        """Testa as_response_model com exclusão de campos."""
        user = TestUser(id="123e4567-e89b-12d3-a456-426614174000", name="John", age=30)
        
        result = as_response_model(user, exclude=['age'])
        
        assert result is not None
        assert result['name'] == "John"
        assert 'age' not in result
        assert str(result['id']) == "123e4567-e89b-12d3-a456-426614174000"
    
    def test_as_response_model_with_include(self):
        """Testa as_response_model com inclusão de campos."""
        user = TestUser(id="123e4567-e89b-12d3-a456-426614174000", name="John", age=30)
        
        result = as_response_model(user, include=['name'])
        
        assert result is not None
        assert result['name'] == "John"
        assert 'age' not in result
        assert 'id' not in result
    
    def test_as_response_models_empty(self):
        """Testa as_response_models com lista vazia."""
        result = as_response_models([])
        assert result == []
    
    def test_as_response_models_multiple(self):
        """Testa as_response_models com múltiplos modelos."""
        users = cast(List[Model], [
            TestUser(id="123e4567-e89b-12d3-a456-426614174000", name="John", age=30),
            TestUser(id="123e4567-e89b-12d3-a456-426614174001", name="Jane", age=25)
        ])
        
        result = as_response_models(users)
        
        assert len(result) == 2
        assert result[0]['name'] == "John"
        assert result[0]['age'] == 30
        assert result[1]['name'] == "Jane"
        assert result[1]['age'] == 25
    
    def test_as_response_models_with_exclude(self):
        """Testa as_response_models com exclusão de campos."""
        users = cast(List[Model], [
            TestUser(id="123e4567-e89b-12d3-a456-426614174000", name="John", age=30),
            TestUser(id="123e4567-e89b-12d3-a456-426614174001", name="Jane", age=25)
        ])
        
        result = as_response_models(users, exclude=['age'])
        
        assert len(result) == 2
        assert result[0]['name'] == "John"
        assert 'age' not in result[0]
        assert result[1]['name'] == "Jane"
        assert 'age' not in result[1]
    
    def test_caspyorm_dependency_init(self):
        """Testa inicialização do CaspyORMDependency."""
        dependency = CaspyORMDependency(auto_connect=True)
        assert dependency.auto_connect is True
    
    def test_caspyorm_dependency_get_session(self):
        """Testa get_session do CaspyORMDependency."""
        with patch('caspyorm.contrib.fastapi.get_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = mock_session
            
            dependency = CaspyORMDependency()
            session = dependency.get_session()
            
            assert session == mock_session
            mock_get_session.assert_called_once()
    
    def test_caspyorm_dependency_get_async_session(self):
        """Testa get_async_session do CaspyORMDependency."""
        with patch('caspyorm.contrib.fastapi.get_async_session') as mock_get_async_session:
            mock_session = Mock()
            mock_get_async_session.return_value = mock_session
            
            dependency = CaspyORMDependency()
            session = dependency.get_async_session()
            
            assert session == mock_session
            mock_get_async_session.assert_called_once()
    
    def test_caspyorm_dependency_call(self):
        """Testa __call__ do CaspyORMDependency."""
        with patch('caspyorm.contrib.fastapi.get_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = mock_session
            
            dependency = CaspyORMDependency()
            session = dependency()
            
            assert session == mock_session
            mock_get_session.assert_called_once()


class TestFastAPIIntegrationWithoutFastAPI:
    """Testes para quando FastAPI não está disponível."""
    
    def test_get_session_fastapi_not_available(self):
        """Testa get_session quando FastAPI não está disponível."""
        with patch('caspyorm.contrib.fastapi.FASTAPI_AVAILABLE', False):
            with pytest.raises(ImportError) as exc_info:
                get_session()
            
            assert "FastAPI não está instalado" in str(exc_info.value)
    
    def test_get_async_session_fastapi_not_available(self):
        """Testa get_async_session quando FastAPI não está disponível."""
        with patch('caspyorm.contrib.fastapi.FASTAPI_AVAILABLE', False):
            with pytest.raises(ImportError) as exc_info:
                get_async_session()
            
            assert "FastAPI não está instalado" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__]) 