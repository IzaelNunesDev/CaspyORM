import pytest
from caspyorm import fields, Model

def test_modelo_valido_cria_schema():
    class Usuario(Model):
        id = fields.UUID(primary_key=True)
        nome = fields.Text()
    
    assert Usuario.__table_name__ == 'usuarios'
    assert 'id' in Usuario.__caspy_schema__['fields']
    assert Usuario.__caspy_schema__['fields']['id']['type'] == 'uuid'
    assert Usuario.__caspy_schema__['primary_keys'] == ['id']

def test_modelo_sem_chave_primaria_falha():
    with pytest.raises(TypeError, match="pelo menos uma 'partition_key' ou 'primary_key'"):
        class ModeloSemPK(Model):
            nome = fields.Text()

def test_campo_required_com_default_falha():
    with pytest.raises(ValueError, match="não pode ser 'required' e ter um 'default'"):
        fields.Text(required=True, default="valor")

def test_modelo_com_partition_key():
    class Evento(Model):
        __table_name__ = 'eventos_teste'
        data = fields.Text(partition_key=True)
        hora = fields.Text(clustering_key=True)
        descricao = fields.Text()
    
    assert Evento.__caspy_schema__['partition_keys'] == ['data']
    assert Evento.__caspy_schema__['clustering_keys'] == ['hora']

def test_modelo_com_nome_tabela_customizado():
    class Produto(Model):
        __table_name__ = 'produtos_custom'
        id = fields.UUID(primary_key=True)
        nome = fields.Text()
    
    assert Produto.__table_name__ == 'produtos_custom'

def test_campo_com_index():
    class Artigo(Model):
        __table_name__ = 'artigos_index'
        id = fields.UUID(primary_key=True)
        titulo = fields.Text(index=True)
        conteudo = fields.Text()
    
    # Verifica se o campo tem a propriedade index
    titulo_field = Artigo.model_fields['titulo']
    assert titulo_field.index is True 