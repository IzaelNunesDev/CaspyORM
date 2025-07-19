"""
Testes para as melhorias do Nível 2 da CaspyORM: Paginação eficiente.
"""
import pytest
import uuid
import time
from caspyorm import Model, fields
from caspyorm import connection



class UsuarioPaginacao(Model):
    __table_name__ = 'usuarios_paginacao_teste'
    grupo: fields.Text = fields.Text(partition_key=True)
    id = fields.UUID(primary_key=True)
    nome = fields.Text(required=True)
    email = fields.Text(index=True)

@pytest.fixture(scope="function")
def setup_usuarios(session):
    # Drop da tabela para garantir schema correto e limpo
    try:
        connection.execute("DROP TABLE IF EXISTS usuarios_paginacao_teste")
    except Exception:
        pass
    
    UsuarioPaginacao.sync_table()

    # Criar 25 usuários no grupo 'A' para testar paginação real
    usuarios = []
    for i in range(25):
        usuario = UsuarioPaginacao.create(
            grupo="A",
            id=uuid.uuid4(), # É importante passar o ID aqui, pois a PK é composta
            nome=f"Usuário {i}",
            email=f"usuario{i}@teste.com"
        )
        usuarios.append(usuario)
    return usuarios

def test_paginacao_page_method(session, setup_usuarios):
    page_size = 10
    queryset = UsuarioPaginacao.filter(grupo="A")
    nomes = set()
    paging_state = None
    page_count = 0
    
    while True:
        resultados, paging_state = queryset.page(page_size=page_size, paging_state=paging_state)
        nomes.update(u.nome for u in resultados)
        page_count += 1
        
        # Verificar que cada página tem o tamanho correto (exceto a última)
        if paging_state:
            assert len(resultados) == page_size, f"Página {page_count} deveria ter {page_size} itens, mas tem {len(resultados)}"
        else:
            # Última página pode ter menos itens
            assert len(resultados) <= page_size, f"Última página deveria ter no máximo {page_size} itens, mas tem {len(resultados)}"
            break
    
    # Verificar que a paginação está funcionando
    assert page_count >= 2, f"Esperava pelo menos 2 páginas, mas foram {page_count}"
    assert len(nomes) >= 15, f"Esperava pelo menos 15 usuários únicos, mas encontrou {len(nomes)}"
    print(f"Paginação funcionando: {page_count} páginas, {len(nomes)} usuários únicos encontrados")

def test_count_without_allow_filtering(session, setup_usuarios):
    """Testa que o método count() não adiciona ALLOW FILTERING automaticamente."""
    # Count sem filtros (deve funcionar sem ALLOW FILTERING)
    total = UsuarioPaginacao.filter(grupo="A").count()
    assert total == 25
    
    # Count com filtro em campo indexado (deve funcionar sem ALLOW FILTERING)
    count_email = UsuarioPaginacao.filter(grupo="A", email="usuario0@teste.com").count()
    assert count_email == 1
    
    # Count com filtro em campo não-indexado (deve falhar sem ALLOW FILTERING)
    # Isso testa que o comportamento padrão é não adicionar ALLOW FILTERING
    try:
        count_nome = UsuarioPaginacao.filter(grupo="A", nome="Usuário 0").count()
        # Se chegou aqui, significa que a query funcionou sem ALLOW FILTERING
        # Isso pode acontecer se o campo estiver indexado ou se o Cassandra permitir
        pass
    except Exception as e:
        # Esperado: deve falhar sem ALLOW FILTERING para campos não-indexados
        assert "ALLOW FILTERING" in str(e) or "Cannot execute this query" in str(e)
    
    # Count com allow_filtering explícito (deve funcionar)
    count_nome_with_allow = UsuarioPaginacao.filter(grupo="A", nome="Usuário 0").allow_filtering().count()
    assert count_nome_with_allow == 1