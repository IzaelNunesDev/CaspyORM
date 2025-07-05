"""
Testes para as melhorias do Nível 2 da CaspyORM: Paginação eficiente.
"""
import pytest
import uuid
from caspyorm import Model, fields
from caspyorm import connection

class UsuarioPaginacao(Model):
    __table_name__ = 'usuarios_paginacao_teste'
    grupo: fields.Text = fields.Text(partition_key=True)
    id: fields.UUID = fields.UUID(primary_key=True)
    nome: fields.Text = fields.Text(required=True)
    email: fields.Text = fields.Text(index=True)

@pytest.fixture(scope="function")
def setup_usuarios(session):
    # Drop da tabela para garantir schema correto
    try:
        connection.execute("DROP TABLE IF EXISTS usuarios_paginacao_teste")
    except Exception:
        pass
    UsuarioPaginacao.sync_table()
    # Limpar tabela antes do teste
    for usuario in UsuarioPaginacao.filter(grupo="A"):
        usuario.delete()
    # Criar 25 usuários no grupo 'A'
    usuarios = []
    for i in range(25):
        usuario = UsuarioPaginacao.create(
            grupo="A",
            nome=f"Usuário {i}",
            email=f"usuario{i}@teste.com"
        )
        usuarios.append(usuario)
    return usuarios

def test_paginacao_page_method(setup_usuarios):
    page_size = 10
    queryset = UsuarioPaginacao.filter(grupo="A")
    nomes = set()
    paging_state = None
    while True:
        resultados, paging_state = queryset.page(page_size=page_size, paging_state=paging_state)
        nomes.update(u.nome for u in resultados)
        if not paging_state:
            break
    assert len(nomes) == 25 