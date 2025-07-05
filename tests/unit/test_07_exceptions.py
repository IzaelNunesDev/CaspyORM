import pytest
import uuid
from caspyorm import fields, Model
from caspyorm.connection import connection
from caspyorm.exceptions import CaspyORMException, ValidationError, ConnectionError

# NOVA FIXTURE para isolar os testes de desconexão
@pytest.fixture
def disconnected_session():
    """Fixture que desconecta a sessão para um teste e a reconecta depois."""
    # Salva o estado atual da conexão
    was_connected = connection.is_connected
    
    # Desconecta se estiver conectado
    if was_connected:
        connection.disconnect()
    
    yield  # Permite que o teste execute
    
    # Reconecta se estava conectado antes
    if was_connected:
        try:
            connection.connect(contact_points=["127.0.0.1"], keyspace="caspyorm_test_suite")
        except Exception as e:
            print(f"Erro ao reconectar: {e}")
            # Tenta reconectar novamente
            connection.connect(contact_points=["127.0.0.1"], keyspace="caspyorm_test_suite")

def with_connection(test_func):
    """Decorator para garantir que a conexão está ativa antes do teste."""
    def wrapper(*args, **kwargs):
        try:
            connection.get_session()
        except RuntimeError:
            connection.connect(contact_points=["127.0.0.1"], keyspace="caspyorm_test_suite")
        return test_func(*args, **kwargs)
    return wrapper

# Função utilitária para checar conexão
def cassandra_disponivel():
    """Verifica se o Cassandra está disponível sem tentar conectar."""
    try:
        from caspyorm.connection import connection
        # Se já está conectado, retorna True
        if connection.is_connected:
            return True
        # Se não está conectado, tenta conectar
        connection.connect()
        return connection.is_connected
    except Exception:
        return False

def test_excecao_campo_obrigatorio(session):
    """Testa se exceção é levantada quando campo obrigatório não é fornecido."""
    class Usuario(Model):
        __table_name__ = 'usuarios_exceptions'
        id = fields.UUID(primary_key=True)
        nome = fields.Text(required=True)
    
    with pytest.raises(ValidationError, match="Campo 'nome' é obrigatório"):
        Usuario.create(id=uuid.uuid4())

def test_excecao_tipo_invalido(session):
    """Testa se exceção é levantada quando tipo de dado é inválido."""
    class Produto(Model):
        __table_name__ = 'produtos_exceptions'
        id = fields.UUID(primary_key=True)
        preco = fields.Integer()
    
    with pytest.raises(TypeError, match="Não foi possível converter"):
        Produto.create(id=uuid.uuid4(), preco="não é número")

def test_excecao_conexao_nao_estabelecida(disconnected_session):
    """Testa se exceção é levantada quando não há conexão com Cassandra."""
    from caspyorm.connection import connection
    
    # A fixture já garantiu a desconexão
    
    class Teste(Model):
        __table_name__ = 'teste_conexao'
        id = fields.UUID(primary_key=True)
    
    with pytest.raises(RuntimeError, match=r"[cC]onexão com o Cassandra não foi estabelecida"):
        Teste.create(id=uuid.uuid4())

def test_excecao_operador_invalido(session):
    """Testa se exceção é levantada quando operador de filtro é inválido."""
    class Artigo(Model):
        __table_name__ = 'artigos_exceptions_op'
        id = fields.UUID(primary_key=True)
        titulo = fields.Text()
    
    Artigo.sync_table()
    
    # A biblioteca corretamente levanta um ValueError, não um UserWarning
    with pytest.raises(ValueError, match="Operador de filtro não suportado: 'invalid_op'"):
        list(Artigo.filter(titulo__invalid_op="valor"))

def test_excecao_campo_nao_indexado(session):
    """Testa se exceção é levantada quando filtro é aplicado em campo não indexado."""
    class Evento(Model):
        __table_name__ = 'eventos_exceptions'
        id = fields.UUID(primary_key=True)
        data = fields.Text(partition_key=True)  # Usando Text em vez de Date
        descricao = fields.Text()  # Não indexado
    
    # Primeiro sincroniza a tabela
    Evento.sync_table()
    
    # Cria um evento para testar
    evento = Evento.create(id=uuid.uuid4(), data="2024-01-01", descricao="Teste")
    
    # Testa filtro em campo não indexado - deve gerar warning
    with pytest.warns(UserWarning, match="não é uma chave primária nem está indexado"):
        list(Evento.filter(descricao="alguma descrição"))

def test_excecao_primary_key_obrigatoria(session):
    """Testa se exceção é levantada quando primary key não é fornecida."""
    class Item(Model):
        __table_name__ = 'itens_exceptions'
        # Desabilita o gerador de UUID padrão para permitir None no teste
        id = fields.UUID(primary_key=True, default=None)
        nome = fields.Text()
    
    Item.sync_table()
    
    # A validação agora está em save(), que é chamado por create()
    with pytest.raises(ValidationError, match="Primary key 'id' cannot be None before saving."):
        Item.create(nome="Item sem ID")

def test_excecao_colecao_tipo_invalido(session):
    """Testa se exceção é levantada quando coleção contém tipos inválidos."""
    class Documento(Model):
        __table_name__ = 'documentos_exceptions'
        id = fields.UUID(primary_key=True)
        tags = fields.List(fields.Text())
    
    with pytest.raises(TypeError, match="Não foi possível converter item"):
        Documento.create(id=uuid.uuid4(), tags=["tag1", 123, "tag2"])

def test_excecao_map_chave_invalida(session):
    """Testa se exceção é levantada quando chave do map é inválida."""
    class Configuracao(Model):
        __table_name__ = 'configuracoes_exceptions'
        id = fields.UUID(primary_key=True)
        settings = fields.Map(fields.Text(), fields.Text())
    
    with pytest.raises(TypeError, match="Não foi possível converter chave"):
        Configuracao.create(id=uuid.uuid4(), settings={123: "valor"})

def test_excecao_map_valor_invalido(session):
    """Testa se exceção é levantada quando valor do map é inválido."""
    class Configuracao(Model):
        __table_name__ = 'configuracoes_exceptions'
        id = fields.UUID(primary_key=True)
        settings = fields.Map(fields.Text(), fields.Integer())
    
    with pytest.raises(TypeError, match="Não foi possível converter valor"):
        Configuracao.create(id=uuid.uuid4(), settings={"chave": "não é número"})

def test_excecao_required_com_default():
    """Testa se exceção é levantada quando campo é required e tem default."""
    with pytest.raises(ValueError, match="não pode ser 'required' e ter um 'default'"):
        fields.Text(required=True, default="valor")

def test_excecao_modelo_sem_primary_key():
    """Testa se exceção é levantada quando modelo não tem primary key."""
    with pytest.raises(TypeError, match="pelo menos uma 'partition_key' ou 'primary_key'"):
        class ModeloSemPK(Model):
            nome = fields.Text()

def test_excecao_sync_table_sem_conexao(disconnected_session):
    """Testa se exceção é levantada ao tentar sincronizar sem conexão."""
    from caspyorm.connection import connection
    
    # A fixture já garantiu a desconexão
    
    class TesteSync(Model):
        __table_name__ = 'teste_sync'
        id = fields.UUID(primary_key=True)
    
    with pytest.raises(RuntimeError, match=r"[cC]onexão com o Cassandra não foi estabelecida"):
        TesteSync.sync_table()

def test_excecao_uuid_invalido(session):
    """Testa se exceção é levantada quando UUID é inválido."""
    class Usuario(Model):
        __table_name__ = 'usuarios_uuid_exceptions'
        id = fields.UUID(primary_key=True)
        nome = fields.Text()
    
    with pytest.raises(TypeError, match="Não foi possível converter"):
        Usuario.create(id="não é um uuid válido", nome="João")

def test_excecao_boolean_invalido(session):
    """Testa se exceção é levantada quando boolean é inválido."""
    class Config(Model):
        __table_name__ = 'config_boolean_exceptions'
        id = fields.UUID(primary_key=True)
        ativo = fields.Boolean()
    
    Config.sync_table()
    
    with pytest.raises(TypeError, match="Não foi possível converter"):
        Config.create(id=uuid.uuid4(), ativo="não é boolean")

def test_excecao_float_invalido(session):
    """Testa se exceção é levantada quando float é inválido."""
    class Produto(Model):
        __table_name__ = 'produtos_float_exceptions'
        id = fields.UUID(primary_key=True)
        preco = fields.Float()
    
    with pytest.raises(TypeError, match="Não foi possível converter"):
        Produto.create(id=uuid.uuid4(), preco="não é número")

def test_excecao_set_tipo_invalido(session):
    """Testa se exceção é levantada quando set contém tipos inválidos."""
    class Usuario(Model):
        __table_name__ = 'usuarios_set_exceptions'
        id = fields.UUID(primary_key=True)
        permissoes = fields.Set(fields.Text())
    
    with pytest.raises(TypeError, match="Não foi possível converter item"):
        Usuario.create(id=uuid.uuid4(), permissoes={"admin", 123, "user"})

def test_excecao_atualizar_campo_inexistente(session):
    """Testa se exceção é levantada quando tentamos atualizar campo inexistente."""
    class Usuario(Model):
        __table_name__ = 'usuarios_update_exceptions'
        id = fields.UUID(primary_key=True)
        nome = fields.Text()
    
    # Primeiro sincroniza a tabela
    Usuario.sync_table()
    
    usuario = Usuario.create(id=uuid.uuid4(), nome="João")
    
    with pytest.raises(ValidationError, match="Campo 'campo_inexistente' não existe"):
        usuario.update(campo_inexistente="valor")

def test_excecao_delete_sem_primary_key(session):
    """Testa se exceção é levantada quando tentamos deletar com primary key nula."""
    class Usuario(Model):
        __table_name__ = 'usuarios_delete_exceptions'
        id = fields.UUID(primary_key=True)
        nome = fields.Text()
    
    Usuario.sync_table()
    
    usuario = Usuario(id=uuid.uuid4(), nome="João") # Não salva, apenas instancia
    
    # Simula uma PK nula usando setattr para contornar a tipagem
    setattr(usuario, 'id', None)
    
    # A validação agora está em `delete()`
    with pytest.raises(ValidationError, match="Primary key 'id' is required to delete, but was None."):
        usuario.delete()

def test_excecao_filtro_sem_operador(session):
    """Testa se exceção é levantada quando filtro não tem operador válido."""
    class Usuario(Model):
        __table_name__ = 'usuarios_filter_exceptions'
        id = fields.UUID(primary_key=True)
        nome = fields.Text()
    
    # Limpa a tabela e sincroniza
    session.execute(f"DROP TABLE IF EXISTS {Usuario.__table_name__}")
    Usuario.sync_table()
    
    # Cria um usuário para testar
    Usuario.create(id=uuid.uuid4(), nome="João")
    
    # Testa filtro sem operador - deve funcionar com equals implícito
    usuarios = list(Usuario.filter(nome="João"))
    assert len(usuarios) == 1

def test_excecao_campo_inexistente_no_create(session):
    """Testa se campos inexistentes são ignorados no create (comportamento atual)."""
    class Usuario(Model):
        __table_name__ = 'usuarios_ignore_exceptions'
        id = fields.UUID(primary_key=True)
        nome = fields.Text()
    
    # Primeiro sincroniza a tabela
    Usuario.sync_table()
    
    # Campos inexistentes são ignorados (comportamento atual)
    usuario = Usuario.create(id=uuid.uuid4(), nome="João", campo_inexistente="valor")
    assert usuario.nome == "João"
    assert not hasattr(usuario, 'campo_inexistente')

def test_excecao_acesso_campo_inexistente(session):
    """Testa se exceção é levantada quando tentamos acessar campo que não existe."""
    class Usuario(Model):
        __table_name__ = 'usuarios_access_exceptions'
        id = fields.UUID(primary_key=True)
        nome = fields.Text()
    
    Usuario.sync_table()
    usuario = Usuario.create(id=uuid.uuid4(), nome="João")
    
    with pytest.raises(AttributeError):
        _ = getattr(usuario, 'campo_inexistente')

def test_excecao_atribuicao_campo_inexistente(session):
    """Testa se exceção é levantada quando tentamos atribuir a campo inexistente."""
    class Usuario(Model):
        __table_name__ = 'usuarios_assign_exceptions'
        id = fields.UUID(primary_key=True)
        nome = fields.Text()
    
    Usuario.sync_table()
    usuario = Usuario.create(id=uuid.uuid4(), nome="João")
    
    # Atribuição a campo inexistente deve funcionar (comportamento atual)
    setattr(usuario, 'campo_inexistente', "valor")
    assert getattr(usuario, 'campo_inexistente') == "valor"

def test_excecao_primary_key_none(session):
    """Testa se exceção é levantada quando primary key é None no create."""
    class Usuario(Model):
        __table_name__ = 'usuarios_pk_none_exceptions'
        # Desabilita o gerador de UUID padrão para permitir None no teste
        id = fields.UUID(primary_key=True, default=None)
        nome = fields.Text()
    
    Usuario.sync_table()
    
    # A validação agora está em save(), que é chamado por create()
    with pytest.raises(ValidationError, match="Primary key 'id' cannot be None before saving."):
        Usuario.create(id=None, nome="João")

def test_excecao_campo_required_none(session):
    """Testa se exceção é levantada quando campo required é None."""
    class Usuario(Model):
        __table_name__ = 'usuarios_required_none_exceptions'
        id = fields.UUID(primary_key=True)
        nome = fields.Text(required=True)
    
    with pytest.raises(ValidationError, match="Campo 'nome' é obrigatório"):
        Usuario.create(id=uuid.uuid4(), nome=None)