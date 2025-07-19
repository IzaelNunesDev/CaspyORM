"""
Testes para as correções críticas implementadas:
1. Remoção do ALLOW FILTERING automático
2. Adição do método allow_filtering() explícito
3. Melhoria na paginação (preparação para paging_state)
"""
import pytest
import uuid
from caspyorm import Model, fields
from caspyorm import connection

class UsuarioTeste(Model):
    __table_name__ = 'usuarios_teste_critico'
    id = fields.UUID(primary_key=True)
    nome = fields.Text(required=True)
    email = fields.Text(index=True)
    ativo = fields.Boolean(default=True)

@pytest.fixture(scope="function")
def setup_usuarios(session):
    # Drop da tabela para garantir schema correto e limpo
    try:
        connection.execute("DROP TABLE IF EXISTS usuarios_teste_critico")
    except Exception:
        pass
    
    UsuarioTeste.sync_table()
    
    # Criar alguns usuários para teste
    usuarios = []
    for i in range(5):
        usuario = UsuarioTeste.create(
            id=uuid.uuid4(),
            nome=f"Usuário {i}",
            email=f"usuario{i}@teste.com",
            ativo=True
        )
        usuarios.append(usuario)
    return usuarios

def test_allow_filtering_nao_automatico(setup_usuarios):
    """Testa que ALLOW FILTERING não é adicionado automaticamente."""
    # Query sem ALLOW FILTERING explícito
    queryset = UsuarioTeste.filter(ativo=True)
    
    # Verificar que a query não contém ALLOW FILTERING
    # Como ativo não é PK, a query deve falhar sem ALLOW FILTERING
    # (Isso é o comportamento esperado após a correção)
    with pytest.raises(Exception):  # Deve falhar sem ALLOW FILTERING
        queryset.all()

def test_allow_filtering_explicito(setup_usuarios):
    """Testa que ALLOW FILTERING pode ser adicionado explicitamente."""
    # Query com ALLOW FILTERING explícito
    queryset = UsuarioTeste.filter(ativo=True).allow_filtering()
    
    # Agora a query deve funcionar
    resultados = queryset.all()
    
    # Deve retornar todos os usuários ativos
    assert len(resultados) == 5
    assert all(getattr(u, 'ativo', False) for u in resultados)

def test_paginacao_basica(setup_usuarios):
    """Testa que a paginação básica ainda funciona."""
    page_size = 2
    queryset = UsuarioTeste.all()
    
    # Primeira página
    resultados, next_paging_state = queryset.page(page_size=page_size)
    
    # Deve retornar resultados
    assert len(resultados) <= page_size
    assert next_paging_state is not None  # Deve ter mais páginas
    
    # Segunda página
    if next_paging_state:
        mais_resultados, final_paging_state = queryset.page(
            page_size=page_size, 
            paging_state=next_paging_state
        )
        # Deve retornar mais resultados
        assert len(mais_resultados) > 0

def test_allow_filtering_encadeamento():
    """Testa que allow_filtering() pode ser encadeado com outros métodos."""
    queryset = UsuarioTeste.filter(ativo=True).allow_filtering().limit(10)
    
    # Deve funcionar sem erro
    assert queryset is not None
    assert hasattr(queryset, '_allow_filtering')
    assert queryset._allow_filtering is True

def test_allow_filtering_clone():
    """Testa que allow_filtering() é copiado corretamente no clone."""
    original = UsuarioTeste.filter(ativo=True).allow_filtering()
    clone = original.filter(nome__exact="teste")
    
    # O clone deve manter a flag allow_filtering
    assert clone._allow_filtering is True 