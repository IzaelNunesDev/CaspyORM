import pytest
import uuid
from caspyorm import fields, Model

class Usuario(Model):
    __table_name__ = 'usuarios_pydantic'
    id = fields.UUID(primary_key=True)
    nome = fields.Text(required=True)
    email = fields.Text()
    ativo = fields.Boolean(default=True)

@pytest.fixture(autouse=True)
def sync_usuario_table(session):
    session.execute(f"DROP TABLE IF EXISTS {Usuario.__table_name__}")
    Usuario.sync_table()

def test_create_pydantic_model():
    """Testa a criação de um modelo Pydantic a partir de um modelo CaspyORM."""
    PydanticUsuario = Usuario.as_pydantic()
    
    # Verifica se o modelo foi criado corretamente
    assert hasattr(PydanticUsuario, '__fields__')
    assert 'id' in PydanticUsuario.__fields__
    assert 'nome' in PydanticUsuario.__fields__
    assert 'email' in PydanticUsuario.__fields__
    assert 'ativo' in PydanticUsuario.__fields__

def test_pydantic_model_validation():
    """Testa a validação de dados com o modelo Pydantic."""
    PydanticUsuario = Usuario.as_pydantic()
    
    # Teste com dados válidos
    dados_validos = {
        'nome': 'João Silva',
        'email': 'joao@email.com',
        'ativo': True
    }
    
    usuario_pydantic = PydanticUsuario(**dados_validos)
    assert usuario_pydantic.nome == 'João Silva'
    assert usuario_pydantic.email == 'joao@email.com'
    assert usuario_pydantic.ativo is True

def test_pydantic_model_com_campos_obrigatorios():
    """Testa se campos obrigatórios são respeitados no modelo Pydantic."""
    PydanticUsuario = Usuario.as_pydantic()
    
    # Teste sem campo obrigatório
    with pytest.raises(ValueError):
        PydanticUsuario(email='teste@email.com')  # nome é obrigatório

def test_pydantic_model_com_valores_default():
    """Testa se valores default são aplicados corretamente."""
    PydanticUsuario = Usuario.as_pydantic()
    
    dados = {'nome': 'Maria'}
    usuario = PydanticUsuario(**dados)
    
    assert usuario.nome == 'Maria'
    assert usuario.ativo is True  # valor default
    assert usuario.email is None  # campo opcional

def test_conversao_entre_modelos():
    """Testa a conversão entre modelo CaspyORM e Pydantic."""
    PydanticUsuario = Usuario.as_pydantic()
    
    # Cria instância CaspyORM
    usuario_caspy = Usuario.create(
        id=uuid.uuid4(),
        nome='Pedro',
        email='pedro@email.com',
        ativo=False
    )
    
    # Converte para Pydantic
    dados_pydantic = {
        'id': usuario_caspy.id,
        'nome': usuario_caspy.nome,
        'email': usuario_caspy.email,
        'ativo': usuario_caspy.ativo
    }
    
    usuario_pydantic = PydanticUsuario(**dados_pydantic)
    assert usuario_pydantic.nome == usuario_caspy.nome
    assert usuario_pydantic.email == usuario_caspy.email
    assert usuario_pydantic.ativo == usuario_caspy.ativo

def test_pydantic_model_com_tipos_especiais():
    """Testa se tipos especiais (UUID, Boolean) são tratados corretamente."""
    PydanticUsuario = Usuario.as_pydantic()
    
    import uuid
    user_id = uuid.uuid4()
    
    dados = {
        'id': user_id,
        'nome': 'Teste',
        'ativo': True
    }
    
    usuario = PydanticUsuario(**dados)
    assert usuario.id == user_id
    assert isinstance(usuario.ativo, bool)

def test_pydantic_model_sem_campos_especiais():
    """Testa modelo Pydantic sem campos especiais do CaspyORM."""
    class ModeloSimples(Model):
        __table_name__ = 'modelo_simples'
        id = fields.UUID(primary_key=True)
        texto = fields.Text()
    
    PydanticModelo = create_pydantic_model(ModeloSimples)
    
    dados = {'texto': 'Texto simples'}
    modelo = PydanticModelo(**dados)
    assert modelo.texto == 'Texto simples' 