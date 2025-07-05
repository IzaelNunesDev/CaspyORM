"""
Testes para as melhorias do Nível 1 da CaspyORM.

Este arquivo testa:
1. Sistema de logging adequado
2. Avisos para filtros em campos não-indexados
3. Garantia de coleções vazias (não None)
4. UPDATE parcial com método update()
"""

import pytest
import warnings
import logging
from caspyorm import Model, fields, connection
from caspyorm.exceptions import ValidationError


class UsuarioTeste(Model):
    """Modelo de teste para verificar as melhorias do Nível 1."""
    __table_name__ = 'usuarios_nivel1_teste'
    
    id: fields.UUID = fields.UUID(primary_key=True)
    nome: fields.Text = fields.Text(required=True)
    email: fields.Text = fields.Text(index=True)
    idade: fields.Integer = fields.Integer()  # Campo não-indexado
    tags: fields.List = fields.List(fields.Text())  # Coleção
    configuracoes: fields.Map = fields.Map(fields.Text(), fields.Text())  # Coleção


class TestNivel1Improvements:
    """Testa as melhorias implementadas no Nível 1."""
    
    def test_01_logging_system(self, session):
        """Testa se o sistema de logging está funcionando."""
        # Capturar logs para verificar se estão sendo gerados
        with self._capture_logs() as log_records:
            # Sincronizar tabela (deve gerar logs)
            UsuarioTeste.sync_table()
            
            # Criar uma instância (deve gerar logs)
            usuario = UsuarioTeste.create(
                nome="João Silva",
                email="joao@teste.com",
                idade=30
            )
        
        # Verificar se logs foram gerados
        assert len(log_records) > 0
        assert any("caspyorm" in record.name for record in log_records)
    
    def test_02_warnings_non_indexed_fields(self, session):
        """Testa se avisos são emitidos para filtros em campos não-indexados."""
        UsuarioTeste.sync_table()
        
        # Criar um usuário para testar
        usuario = UsuarioTeste.create(
            nome="Maria Santos",
            email="maria@teste.com",
            idade=25
        )
        
        # Capturar warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Filtrar por campo não-indexado (deve gerar warning)
            usuarios = UsuarioTeste.filter(idade=25)
            list(usuarios)  # Executar a query
            
            # Verificar se o warning foi emitido
            assert len(w) > 0
            warning_messages = [str(warning.message) for warning in w]
            assert any("idade" in msg and "não é uma chave primária" in msg for msg in warning_messages)
    
    def test_03_empty_collections_not_none(self, session):
        """Testa se coleções são inicializadas como vazias, não None."""
        UsuarioTeste.sync_table()
        
        # Criar usuário sem fornecer coleções
        usuario = UsuarioTeste.create(
            nome="Pedro Costa",
            email="pedro@teste.com"
        )
        
        # Verificar se as coleções são inicializadas como vazias
        assert usuario.tags == []
        assert usuario.configuracoes == {}
        
        # Verificar se não são None
        assert usuario.tags is not None
        assert usuario.configuracoes is not None
    
    def test_04_partial_update_method(self, session):
        """Testa o método update() para atualização parcial."""
        UsuarioTeste.sync_table()
        
        # Criar usuário
        usuario = UsuarioTeste.create(
            nome="Ana Oliveira",
            email="ana@teste.com",
            idade=28,
            tags=["desenvolvedor", "python"],
            configuracoes={"tema": "escuro"}
        )
        
        # Fazer update parcial
        usuario.update(
            idade=29,
            tags=["desenvolvedor", "python", "cassandra"]
        )
        
        # Verificar se apenas os campos especificados foram atualizados
        assert usuario.idade == 29
        assert usuario.tags == ["desenvolvedor", "python", "cassandra"]
        assert usuario.nome == "Ana Oliveira"  # Não deve ter mudado
        assert usuario.email == "ana@teste.com"  # Não deve ter mudado
        assert usuario.configuracoes == {"tema": "escuro"}  # Não deve ter mudado
        
        # Verificar se os dados foram persistidos no banco
        usuario_atualizado = UsuarioTeste.get(id=usuario.id)
        assert usuario_atualizado.idade == 29
        assert usuario_atualizado.tags == ["desenvolvedor", "python", "cassandra"]
    
    def test_05_update_validation(self, session):
        """Testa validação no método update()."""
        UsuarioTeste.sync_table()
        
        usuario = UsuarioTeste.create(
            nome="Carlos Lima",
            email="carlos@teste.com"
        )
        
        # Tentar atualizar campo inexistente
        with pytest.raises(ValidationError, match="Campo 'campo_inexistente' não existe"):
            usuario.update(campo_inexistente="valor")
        
        # Tentar atualizar com valor inválido
        with pytest.raises(ValidationError):
            usuario.update(idade="não é um número")
    
    def test_06_update_empty_fields(self, session):
        """Testa update() com campos vazios."""
        UsuarioTeste.sync_table()
        
        usuario = UsuarioTeste.create(
            nome="Lucia Ferreira",
            email="lucia@teste.com"
        )
        
        # Update sem campos deve gerar warning mas não falhar
        with self._capture_logs() as log_records:
            result = usuario.update()
        
        assert result == usuario  # Deve retornar a instância
        assert any("update() chamado sem campos" in record.getMessage() for record in log_records)
    
    def test_07_logging_integration(self, session):
        """Testa integração completa do sistema de logging."""
        UsuarioTeste.sync_table()
        
        with self._capture_logs() as log_records:
            # Operações que devem gerar logs
            usuario = UsuarioTeste.create(
                nome="Roberto Alves",
                email="roberto@teste.com"
            )
            
            usuario.update(nome="Roberto Silva")
            
            usuario.delete()
        
        # Verificar se logs informativos foram gerados
        log_messages = [record.getMessage() for record in log_records]
        assert any("Instância salva" in msg for msg in log_messages)
        assert any("Instância atualizada" in msg for msg in log_messages)
        assert any("Instância deletada" in msg for msg in log_messages)
    
    def _capture_logs(self):
        """Context manager para capturar logs durante os testes."""
        class LogCapture:
            def __init__(self):
                self.records = []
                self.handler = None
            
            def __enter__(self):
                self.handler = logging.Handler()
                self.handler.emit = lambda record: self.records.append(record)
                logging.getLogger("caspyorm").addHandler(self.handler)
                return self.records
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                logging.getLogger("caspyorm").removeHandler(self.handler)
        
        return LogCapture()