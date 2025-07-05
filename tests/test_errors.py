# tests/test_errors.py

import pytest
import uuid
from caspyorm import fields, Model, connection
from caspyorm.exceptions import ObjectNotFound, ConnectionError, ValidationError, QueryError

# --- Fixture para garantir conexão ativa antes de cada teste ---
@pytest.fixture(autouse=True)
def ensure_connection():
    try:
        connection.connect(contact_points=['127.0.0.1'], keyspace='caspyorm_test_errors')
    except Exception:
        pass
    yield

# --- Setup e Teardown para os testes ---

@pytest.fixture(scope="module", autouse=True)
def setup_cassandra_connection():
    """Garante que a conexão seja estabelecida antes dos testes e encerrada depois."""
    try:
        connection.connect(contact_points=['127.0.0.1'], keyspace='caspyorm_test_errors')
        yield
    finally:
        try:
            connection.disconnect()
        except:
            pass

# --- Testes de Definição de Modelo Inválida ---

def test_modelo_sem_chave_primaria():
    """
    Deve levantar TypeError se um modelo for definido sem nenhuma chave primária/de partição.
    """
    with pytest.raises(TypeError, match="O modelo deve ter pelo menos uma 'partition_key' ou 'primary_key'"):
        class ModeloInvalido(Model):
            nome: fields.Text = fields.Text()

def test_campo_com_required_e_default():
    """
    Deve levantar ValueError se um campo for definido como 'required' e 'default' ao mesmo tempo.
    """
    with pytest.raises(ValueError, match="Um campo não pode ser 'required' e ter um 'default' ao mesmo tempo"):
        class OutroModeloInvalido(Model):
            id: fields.UUID = fields.UUID(primary_key=True)
            status: fields.Text = fields.Text(required=True, default="ativo")

def test_campo_list_com_tipo_invalido():
    """
    Deve levantar TypeError se um campo List for criado com um tipo inválido.
    """
    with pytest.raises(TypeError, match="O campo interno de uma Lista deve ser uma instância de BaseField"):
        class ModeloComListaInvalida(Model):
            id: fields.UUID = fields.UUID(primary_key=True)
            tags: fields.List = fields.List("texto")  # Deveria ser fields.Text()

# --- Testes de Validação de Query ---

class Tarefa(Model):
    __table_name__ = "tarefas_teste_erros"
    projeto: fields.Text = fields.Text(partition_key=True)
    id: fields.UUID = fields.UUID(clustering_key=True, default=uuid.uuid4)
    descricao: fields.Text = fields.Text()
    status: fields.Text = fields.Text(default="pendente")

def test_delete_sem_chave_de_particao_completa():
    """
    Deve levantar ValueError ao tentar deletar sem a chave de partição completa.
    """
    Tarefa.sync_table(auto_apply=True, verbose=False)
    
    # Tenta deletar usando apenas uma parte da PK (não a chave de partição)
    with pytest.raises(ValueError, match="Para deletar, você deve especificar todos os campos da chave de partição"):
        Tarefa.filter(id=uuid.uuid4()).delete()

def test_filtro_com_operador_invalido():
    """
    Deve levantar ValueError se um operador de filtro desconhecido for usado.
    """
    Tarefa.sync_table(auto_apply=True, verbose=False)
    
    with pytest.raises(ValueError, match="Operador de filtro não suportado"):
        Tarefa.filter(descricao__nonexistent="texto").all()

def test_filtro_em_campo_inexistente():
    """
    Deve levantar cassandra.InvalidRequest se tentar filtrar por um campo que não existe.
    """
    Tarefa.sync_table(auto_apply=True, verbose=False)
    
    with pytest.raises(Exception, match="Undefined column name campo_inexistente"):
        Tarefa.filter(campo_inexistente="valor").all()

# --- Testes de Conexão ---

def test_query_sem_conexao():
    """
    Deve levantar RuntimeError se uma query for executada antes de conectar.
    """
    # Garante que estamos desconectados
    try:
        connection.disconnect()
    except:
        pass
        
    class ModeloDesconectado(Model):
        id: fields.UUID = fields.UUID(primary_key=True)

    with pytest.raises(RuntimeError, match="A conexão com o Cassandra não foi estabelecida"):
        ModeloDesconectado.sync_table()

def test_save_sem_conexao():
    """
    Deve levantar RuntimeError se tentar salvar sem conexão.
    """
    # Garante que estamos desconectados
    try:
        connection.disconnect()
    except:
        pass
    
    class ModeloSemConexao(Model):
        id: fields.UUID = fields.UUID(primary_key=True)
        nome: fields.Text = fields.Text()
    
    modelo = ModeloSemConexao(id=uuid.uuid4(), nome="teste")
    
    with pytest.raises(RuntimeError, match="A conexão com o Cassandra não foi estabelecida"):
        modelo.save()

# --- Testes de Validação de Dados ---

def test_campo_required_sem_valor():
    """
    Deve levantar ValidationError se um campo required não for fornecido.
    """
    class UsuarioRequired(Model):
        __table_name__ = "usuarios_required_test"
        id: fields.UUID = fields.UUID(primary_key=True)
        nome: fields.Text = fields.Text(required=True)
        email: fields.Text = fields.Text(required=True)
    
    UsuarioRequired.sync_table(auto_apply=True, verbose=False)
    
    # Tentar criar sem o campo required
    with pytest.raises(ValidationError, match="Campo 'nome' é obrigatório"):
        UsuarioRequired.create(id=uuid.uuid4(), email="teste@teste.com")

def test_tipo_de_dado_invalido():
    """
    Deve levantar TypeError se um tipo de dado inválido for fornecido.
    """
    class UsuarioTipo(Model):
        __table_name__ = "usuarios_tipo_test"
        id: fields.UUID = fields.UUID(primary_key=True)
        idade: fields.Integer = fields.Integer()
    
    UsuarioTipo.sync_table(auto_apply=True, verbose=False)
    
    # Tentar criar com tipo inválido
    with pytest.raises(TypeError, match="Não foi possível converter"):
        UsuarioTipo.create(id=uuid.uuid4(), idade="não é um número")

# --- Teste de Get retornando None (não é um erro, mas valida o comportamento) ---

def test_get_nao_encontrado_retorna_none():
    """
    O método .get() deve retornar None se nenhum objeto for encontrado, sem levantar erro.
    """
    Tarefa.sync_table(auto_apply=True, verbose=False)
    resultado = Tarefa.get(projeto="projeto_inexistente", id=uuid.uuid4())
    assert resultado is None

# --- Testes de Coleções ---

def test_list_com_tipo_invalido():
    """
    Deve levantar TypeError se uma lista contiver tipos inválidos.
    """
    class ArtigoComTags(Model):
        __table_name__ = "artigos_tags_test"
        id: fields.UUID = fields.UUID(primary_key=True)
        tags: fields.List = fields.List(fields.Text())
    
    ArtigoComTags.sync_table(auto_apply=True, verbose=False)
    
    # Tentar criar com tipos inválidos na lista
    with pytest.raises(TypeError, match="Não foi possível converter"):
        ArtigoComTags.create(id=uuid.uuid4(), tags=[123, "texto", 456])  # 123 e 456 não são strings

def test_map_com_tipos_invalidos():
    """
    Deve levantar TypeError se um map contiver tipos inválidos.
    """
    class Configuracao(Model):
        __table_name__ = "configuracoes_test"
        id: fields.UUID = fields.UUID(primary_key=True)
        config: fields.Map = fields.Map(fields.Text(), fields.Integer())
    
    Configuracao.sync_table(auto_apply=True, verbose=False)
    
    # Tentar criar com tipos inválidos no map
    with pytest.raises(TypeError, match="Não foi possível converter"):
        Configuracao.create(id=uuid.uuid4(), config={"chave": "não é número"})

# --- Testes de Schema ---

def test_sync_table_com_chave_primaria_invalida():
    """
    Deve levantar TypeError se tentar criar um modelo sem chave primária válida.
    """
    with pytest.raises(TypeError, match="O modelo deve ter pelo menos uma 'partition_key' ou 'primary_key'"):
        class ModeloSemPK(Model):
            __table_name__ = "modelo_sem_pk_test"
            nome: fields.Text = fields.Text()
            email: fields.Text = fields.Text() 