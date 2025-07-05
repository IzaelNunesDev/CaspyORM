import uuid
import pytest
from caspyorm import fields, Model

class Artigo(Model):
    __table_name__ = 'artigos_collections'
    id = fields.UUID(primary_key=True)
    tags_list = fields.List(fields.Text())
    colaboradores_set = fields.Set(fields.Text())
    metadados_map = fields.Map(fields.Text(), fields.Text())

@pytest.fixture(autouse=True)
def sync_artigo_table(session):
    session.execute(f"DROP TABLE IF EXISTS {Artigo.__table_name__}")
    Artigo.sync_table()

def test_crud_com_collections():
    artigo_id = uuid.uuid4()
    tags = ["python", "cassandra"]
    colabs = {"ana", "bruno"}
    meta = {"versao": "1.0", "revisado": "true"}
    
    Artigo.create(id=artigo_id, tags_list=tags, colaboradores_set=colabs, metadados_map=meta)
    
    artigo_buscado = Artigo.get(id=artigo_id)
    assert artigo_buscado is not None
    assert sorted(artigo_buscado.tags_list) == sorted(tags)
    assert artigo_buscado.colaboradores_set == colabs
    assert artigo_buscado.metadados_map == meta

def test_collections_nulas_e_vazias():
    artigo_id = uuid.uuid4()
    Artigo.create(id=artigo_id, tags_list=None, colaboradores_set=None, metadados_map=None)
    
    artigo_buscado = Artigo.get(id=artigo_id)
    assert artigo_buscado is not None
    assert artigo_buscado.tags_list == []
    assert artigo_buscado.colaboradores_set == set()
    assert artigo_buscado.metadados_map == {}

def test_list_com_tipos_incorretos():
    artigo_id = uuid.uuid4()
    with pytest.raises(ValueError, match="Todos os itens da lista devem ser do tipo"):
        Artigo.create(id=artigo_id, tags_list=["python", 123, "cassandra"])

def test_set_com_tipos_incorretos():
    artigo_id = uuid.uuid4()
    with pytest.raises(ValueError, match="Todos os itens do set devem ser do tipo"):
        Artigo.create(id=artigo_id, colaboradores_set={"ana", 456, "bruno"})

def test_map_com_tipos_incorretos():
    artigo_id = uuid.uuid4()
    with pytest.raises(ValueError, match="Todas as chaves do map devem ser do tipo"):
        Artigo.create(id=artigo_id, metadados_map={123: "valor", "chave": "valor"})

def test_map_com_valores_incorretos():
    artigo_id = uuid.uuid4()
    with pytest.raises(ValueError, match="Todos os valores do map devem ser do tipo"):
        Artigo.create(id=artigo_id, metadados_map={"chave": 789, "outra": "valor"})

def test_update_collections():
    artigo_id = uuid.uuid4()
    artigo = Artigo.create(id=artigo_id, tags_list=["python"], colaboradores_set={"ana"})
    
    # Atualiza as coleções
    artigo.tags_list.append("cassandra")
    artigo.colaboradores_set.add("bruno")
    artigo.save()
    
    artigo_atualizado = Artigo.get(id=artigo_id)
    assert "cassandra" in artigo_atualizado.tags_list
    assert "bruno" in artigo_atualizado.colaboradores_set 