import pytest
import time
from caspyorm import fields, Model
import uuid

def wait_for_column(session, keyspace, table, column, timeout=5, should_exist=True):
    """
    Aguarda até que uma coluna apareça ou desapareça do schema.
    
    Args:
        session: Sessão do Cassandra
        keyspace: Nome do keyspace
        table: Nome da tabela
        column: Nome da coluna
        timeout: Timeout em segundos
        should_exist: True se espera que a coluna exista, False se espera que não exista
    
    Returns:
        bool: True se a condição foi atendida dentro do timeout
    """
    for _ in range(timeout):
        result = session.execute(f"""
            SELECT column_name FROM system_schema.columns
            WHERE keyspace_name = '{keyspace}'
            AND table_name = '{table}'
            AND column_name = '{column}'
        """)
        
        exists = result.one() is not None
        
        if exists == should_exist:
            return True
            
        time.sleep(1)
    
    return False

class ProdutoOriginal(Model):
    __table_name__ = 'produtos_sync'
    id = fields.UUID(primary_key=True)
    nome = fields.Text()

@pytest.fixture(autouse=True)
def limpar_tabela(session):
    """Limpa a tabela antes de cada teste."""
    session.execute(f"DROP TABLE IF EXISTS produtos_sync")
    yield
    session.execute(f"DROP TABLE IF EXISTS produtos_sync")

def test_sync_table_cria_tabela(session):
    """Testa se sync_table cria a tabela quando ela não existe."""
    ProdutoOriginal.sync_table()
    
    # Verifica se a tabela foi criada
    result = session.execute(f"""
        SELECT table_name FROM system_schema.tables 
        WHERE keyspace_name = '{session.keyspace}' 
        AND table_name = 'produtos_sync'
    """)
    
    assert result.one() is not None

def test_sync_table_com_campo_novo(session):
    """Testa se sync_table adiciona novos campos."""
    # Cria tabela inicial
    ProdutoOriginal.sync_table()
    
    # Redefine o modelo com um campo adicional
    class ProdutoAtualizado(Model):
        __table_name__ = 'produtos_sync'
        id = fields.UUID(primary_key=True)
        nome = fields.Text()
        preco = fields.Float()  # Substituído Decimal por Float
    
    # Sincroniza novamente (com auto_apply para aplicar mudanças)
    ProdutoAtualizado.sync_table(auto_apply=True)
    
    # Verifica se o campo foi adicionado
    # Como o sync_table recria a tabela, vamos verificar se a tabela foi criada com o campo correto
    result = session.execute(f"""
        SELECT column_name FROM system_schema.columns 
        WHERE keyspace_name = '{session.keyspace}' 
        AND table_name = 'produtos_sync'
    """)
    
    columns = [row.column_name for row in result]
    assert 'preco' in columns, f"Campo 'preco' não encontrado. Colunas: {columns}"

def test_sync_table_com_campo_removido(session):
    """
    Testa se sync_table AVISA sobre campos a serem removidos,
    mas NÃO os remove automaticamente por segurança.
    """
    import logging
    from io import StringIO
    
    # Captura logs diretamente do logger da CaspyORM
    log_stream = StringIO()
    log_handler = logging.StreamHandler(log_stream)
    log_handler.setLevel(logging.WARNING)
    
    # Adiciona handler temporário ao logger da CaspyORM
    caspy_logger = logging.getLogger("caspyorm._internal.schema_sync")
    original_handlers = caspy_logger.handlers.copy()
    caspy_logger.addHandler(log_handler)
    
    try:
        # Cria tabela com campo extra
        class ProdutoComExtra(Model):
            __table_name__ = 'produtos_sync'
            id = fields.UUID(primary_key=True)
            nome = fields.Text()
            extra = fields.Text()  # Campo que será removido

        ProdutoComExtra.sync_table()

        # Redefine sem o campo extra
        class ProdutoSemExtra(Model):
            __table_name__ = 'produtos_sync'
            id = fields.UUID(primary_key=True)
            nome = fields.Text()

        # Sincroniza novamente
        ProdutoSemExtra.sync_table(auto_apply=True)

        # 1. Verifica se o AVISO foi logado
        log_text = log_stream.getvalue()
        assert "A remoção automática de colunas não é suportada" in log_text, f"Log não encontrado. Logs capturados: {log_text}"
        assert "ALTER TABLE produtos_sync DROP extra" in log_text, f"Comando DROP não encontrado. Logs capturados: {log_text}"
        
        # 2. Verifica se a coluna NÃO foi removida (comportamento seguro)
        result = session.execute(f"""
            SELECT column_name FROM system_schema.columns 
            WHERE keyspace_name = '{session.keyspace}' 
            AND table_name = 'produtos_sync'
        """)
        
        columns = [row.column_name for row in result]
        assert 'extra' in columns, "A coluna 'extra' foi removida, o que não é o comportamento esperado por segurança."
    
    finally:
        # Restaura handlers originais
        caspy_logger.handlers = original_handlers

def test_sync_table_preserva_dados(session):
    """Testa se sync_table preserva dados existentes ao adicionar campos."""
    # Cria tabela inicial e insere dados
    ProdutoOriginal.sync_table()
    produto_id = uuid.uuid4()
    ProdutoOriginal.create(id=produto_id, nome="Produto Original")
    
    # Redefine com campo adicional
    class ProdutoComPreco(Model):
        __table_name__ = 'produtos_sync'
        id = fields.UUID(primary_key=True)
        nome = fields.Text()
        preco = fields.Float()  # Substituído Decimal por Float
    
    # Sincroniza
    ProdutoComPreco.sync_table()
    
    # Verifica se os dados foram preservados
    produto = ProdutoComPreco.get(id=produto_id)
    assert produto is not None
    assert produto.nome == "Produto Original"

def test_sync_table_com_tipo_diferente(session):
    """Testa se sync_table detecta mudanças de tipo."""
    # Cria tabela com campo Integer
    class ProdutoComInt(Model):
        __table_name__ = 'produtos_sync'
        id = fields.UUID(primary_key=True)
        quantidade = fields.Integer()
    
    ProdutoComInt.sync_table()
    
    # Redefine com campo Text
    class ProdutoComText(Model):
        __table_name__ = 'produtos_sync'
        id = fields.UUID(primary_key=True)
        quantidade = fields.Text()  # Mudança de tipo
    
    # Sincroniza - deve manter o tipo original
    ProdutoComText.sync_table()
    
    # Verifica se o tipo foi mantido como Integer
    result = session.execute(f"""
        SELECT type FROM system_schema.columns 
        WHERE keyspace_name = '{session.keyspace}' 
        AND table_name = 'produtos_sync'
        AND column_name = 'quantidade'
    """)
    
    assert result.one().type == 'int'