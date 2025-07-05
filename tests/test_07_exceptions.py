import pytest
import uuid
from caspyorm import fields, Model
from caspyorm.exceptions import CaspyORMException, ValidationError, ConnectionError

def test_excecao_campo_obrigatorio():
    """Testa se exceção é levantada quando campo obrigatório não é fornecido."""
    class Usuario(Model):
        __table_name__ = 'usuarios_exceptions'
        id = fields.UUID(primary_key=True)
        nome = fields.Text(required=True)
    
    with pytest.raises(ValidationError, match="Campo 'nome' é obrigatório"):
        Usuario.create(id=uuid.uuid4())

def test_excecao_tipo_invalido():
    """Testa se exceção é levantada quando tipo de dado é inválido."""
    class Produto(Model):
        __table_name__ = 'produtos_exceptions'
        id = fields.UUID(primary_key=True)
        preco = fields.Integer()
    
    with pytest.raises(ValidationError, match="Campo 'preco' deve ser do tipo"):
        Produto.create(id=uuid.uuid4(), preco="não é número")

def test_excecao_campo_inexistente():
    """Testa se exceção é levantada quando campo não existe no modelo."""
    class Cliente(Model):
        __table_name__ = 'clientes_exceptions'
        id = fields.UUID(primary_key=True)
        nome = fields.Text()
    
    with pytest.raises(ValidationError, match="Campo 'campo_inexistente' não existe"):
        Cliente.create(id=uuid.uuid4(), nome="João", campo_inexistente="valor")

def test_excecao_conexao_nao_estabelecida():
    """Testa se exceção é levantada quando não há conexão com Cassandra."""
    from caspyorm.connection import connection
    
    # Desconecta se estiver conectado
    if connection.is_connected:
        connection.disconnect()
    
    class Teste(Model):
        __table_name__ = 'teste_conexao'
        id = fields.UUID(primary_key=True)
    
    with pytest.raises(ConnectionError, match="Conexão com Cassandra não estabelecida"):
        Teste.create(id=uuid.uuid4())

def test_excecao_operador_invalido():
    """Testa se exceção é levantada quando operador de filtro é inválido."""
    class Artigo(Model):
        __table_name__ = 'artigos_exceptions'
        id = fields.UUID(primary_key=True)
        titulo = fields.Text()
    
    with pytest.raises(ValueError, match="Operador 'invalid_op' não é suportado"):
        Artigo.filter(titulo__invalid_op="valor")

def test_excecao_campo_nao_indexado():
    """Testa se exceção é levantada quando filtro é aplicado em campo não indexado."""
    class Evento(Model):
        __table_name__ = 'eventos_exceptions'
        id = fields.UUID(primary_key=True)
        data = fields.Date(partition_key=True)
        descricao = fields.Text()  # Não indexado
    
    with pytest.raises(ValueError, match="Campo 'descricao' não é indexado"):
        Evento.filter(descricao="alguma descrição")

def test_excecao_primary_key_obrigatoria():
    """Testa se exceção é levantada quando primary key não é fornecida."""
    class Item(Model):
        __table_name__ = 'itens_exceptions'
        id = fields.UUID(primary_key=True)
        nome = fields.Text()
    
    with pytest.raises(ValidationError, match="Primary key 'id' é obrigatória"):
        Item.create(nome="Item sem ID")

def test_excecao_colecao_tipo_invalido():
    """Testa se exceção é levantada quando coleção contém tipos inválidos."""
    class Documento(Model):
        __table_name__ = 'documentos_exceptions'
        id = fields.UUID(primary_key=True)
        tags = fields.List(fields.Text())
    
    with pytest.raises(ValidationError, match="Todos os itens da lista devem ser do tipo"):
        Documento.create(id=uuid.uuid4(), tags=["tag1", 123, "tag2"])

def test_excecao_map_chave_invalida():
    """Testa se exceção é levantada quando chave do map é inválida."""
    class Configuracao(Model):
        __table_name__ = 'configuracoes_exceptions'
        id = fields.UUID(primary_key=True)
        settings = fields.Map(fields.Text(), fields.Text())
    
    with pytest.raises(ValidationError, match="Todas as chaves do map devem ser do tipo"):
        Configuracao.create(id=uuid.uuid4(), settings={123: "valor"})

def test_excecao_map_valor_invalido():
    """Testa se exceção é levantada quando valor do map é inválido."""
    class Configuracao(Model):
        __table_name__ = 'configuracoes_exceptions'
        id = fields.UUID(primary_key=True)
        settings = fields.Map(fields.Text(), fields.Integer())
    
    with pytest.raises(ValidationError, match="Todos os valores do map devem ser do tipo"):
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

def test_excecao_sync_table_sem_conexao():
    """Testa se exceção é levantada ao tentar sincronizar sem conexão."""
    from caspyorm.connection import connection
    
    # Desconecta se estiver conectado
    if connection.is_connected:
        connection.disconnect()
    
    class TesteSync(Model):
        __table_name__ = 'teste_sync'
        id = fields.UUID(primary_key=True)
    
    with pytest.raises(ConnectionError, match="Conexão com Cassandra não estabelecida"):
        TesteSync.sync_table() 