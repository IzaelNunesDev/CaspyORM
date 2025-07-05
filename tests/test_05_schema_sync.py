import pytest
from caspyorm import fields, Model
import uuid

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
    
    # Sincroniza novamente
    ProdutoAtualizado.sync_table()
    
    # Verifica se o campo foi adicionado
    result = session.execute(f"""
        SELECT column_name FROM system_schema.columns 
        WHERE keyspace_name = '{session.keyspace}' 
        AND table_name = 'produtos_sync'
        AND column_name = 'preco'
    """)
    
    assert result.one() is not None

def test_sync_table_com_campo_removido(session):
    """Testa se sync_table remove campos que não existem mais no modelo."""
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
    ProdutoSemExtra.sync_table()
    
    # Verifica se o campo foi removido
    result = session.execute(f"""
        SELECT column_name FROM system_schema.columns 
        WHERE keyspace_name = '{session.keyspace}' 
        AND table_name = 'produtos_sync'
        AND column_name = 'extra'
    """)
    
    assert result.one() is None

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