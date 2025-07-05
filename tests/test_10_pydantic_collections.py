import pytest
from caspyorm import Model, fields
from caspyorm._internal.serialization import generate_pydantic_model

class ModeloColecoes(Model):
    __table_name__ = 'colecoes_teste'
    id: fields.UUID = fields.UUID(primary_key=True)
    tags: fields.List = fields.List(fields.Text())
    favoritos: fields.Set = fields.Set(fields.Text())
    config: fields.Map = fields.Map(fields.Text(), fields.Text())

def test_generate_pydantic_model_collections():
    PydModel = generate_pydantic_model(ModeloColecoes)
    # Testar criação válida
    obj = PydModel(
        id="123e4567-e89b-12d3-a456-426614174000",
        tags=["python", "cassandra"],
        favoritos={"fastapi", "pytest"},
        config={"tema": "escuro", "lang": "pt"}
    )
    assert obj.id
    assert obj.tags == ["python", "cassandra"]
    assert obj.favoritos == {"fastapi", "pytest"}
    assert obj.config["tema"] == "escuro"
    # Testar validação automática
    with pytest.raises(Exception):
        PydModel(tags="não é lista", favoritos=123, config="não é dict", id="123e4567-e89b-12d3-a456-426614174000") 