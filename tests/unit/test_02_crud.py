import uuid
import pytest
from caspyorm import fields, Model
from caspyorm.exceptions import ValidationError

# Modelo a ser usado nos testes de CRUD
class Produto(Model):
    __table_name__ = 'produtos_crud'
    id = fields.UUID(primary_key=True)
    nome = fields.Text(required=True)
    quantidade = fields.Integer(default=0)

@pytest.fixture(autouse=True)
def sync_produto_table(session):
    """Garante que a tabela exista antes de cada teste neste módulo."""
    session.execute(f"DROP TABLE IF EXISTS {Produto.__table_name__}")
    Produto.sync_table()

def test_create_e_get():
    produto_id = uuid.uuid4()
    produto = Produto.create(id=produto_id, nome="Laptop", quantidade=10)
    
    assert produto.id == produto_id
    assert produto.nome == "Laptop"

    produto_buscado = Produto.get(id=produto_id)
    assert produto_buscado is not None
    assert produto_buscado.id == produto_id
    assert produto_buscado.nome == "Laptop"

def test_save_para_update():
    produto_id = uuid.uuid4()
    produto = Produto.create(id=produto_id, nome="Mouse", quantidade=50)

    # Modifica e salva
    produto.quantidade = 45
    produto.save()

    produto_atualizado = Produto.get(id=produto_id)
    assert produto_atualizado.quantidade == 45

def test_delete_instancia():
    produto_id = uuid.uuid4()
    produto = Produto.create(id=produto_id, nome="Teclado")
    
    produto.delete()
    
    produto_deletado = Produto.get(id=produto_id)
    assert produto_deletado is None

def test_create_com_campos_obrigatorios():
    produto_id = uuid.uuid4()
    produto = Produto.create(id=produto_id, nome="Monitor")
    
    assert produto.nome == "Monitor"
    assert produto.quantidade == 0  # valor default

def test_get_inexistente():
    produto_id = uuid.uuid4()
    produto = Produto.get(id=produto_id)
    assert produto is None

def test_campo_required_sem_valor_falha():
    produto_id = uuid.uuid4()
    with pytest.raises(ValidationError, match="Campo 'nome' é obrigatório"):
        Produto.create(id=produto_id)  # nome é required mas não foi fornecido 