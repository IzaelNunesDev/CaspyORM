import uuid
from caspyorm import fields, Model, connection

# 1. Conexão e limpeza
connection.connect(contact_points=['127.0.0.1'], keyspace='caspyorm_collections_test')
session = connection.get_session()
session.execute("DROP TABLE IF EXISTS artigos")
session.execute("DROP TABLE IF EXISTS configs")

# 2. Modelo com Set e Map
class Artigo(Model):
    __table_name__ = "artigos"
    id: fields.UUID = fields.UUID(primary_key=True)
    titulo: fields.Text = fields.Text(required=True)
    tags: fields.Set = fields.Set(fields.Text())
    notas: fields.Map = fields.Map(fields.Text(), fields.Integer())

Artigo.sync_table()
print("Modelo Artigo sincronizado.")
print("Schema interno do Artigo:", Artigo.__caspy_schema__)

# 3. Inserir dados com Set e Map
print("\n--- Inserindo um artigo com tags e notas ---")
artigo_id = uuid.uuid4()
tags_para_artigo = {"python", "cassandra", "orm"}
notas_para_artigo = {"leitura": 10, "execução": 8}

artigo_novo = Artigo.create(
    id=artigo_id,
    titulo="Coleções no Cassandra",
    tags=tags_para_artigo,
    notas=notas_para_artigo
)
print(f"Artigo criado: {artigo_novo}")
assert artigo_novo.tags == tags_para_artigo
assert artigo_novo.notas == notas_para_artigo

# 4. Buscar e verificar os campos de coleção
print("\n--- Buscando o artigo e verificando as coleções ---")
artigo_buscado = Artigo.get(id=artigo_id)
print(f"Artigo buscado: {artigo_buscado}")

assert artigo_buscado is not None
assert isinstance(artigo_buscado.tags, set)
assert artigo_buscado.tags == tags_para_artigo
assert isinstance(artigo_buscado.notas, dict)
assert artigo_buscado.notas == notas_para_artigo
print("✅ Os campos de coleção foram salvos e recuperados corretamente!")

# 5. Testando casos especiais
print("\n--- Testando casos especiais ---")
artigo_vazio_id = uuid.uuid4()
Artigo.create(id=artigo_vazio_id, titulo="Artigo vazio", tags=set(), notas={})
artigo_recuperado1 = Artigo.get(id=artigo_vazio_id)
print(f"Artigo com set/map vazios: {artigo_recuperado1}")
assert artigo_recuperado1.tags == set()
assert artigo_recuperado1.notas == {}

artigo_null_id = uuid.uuid4()
Artigo.create(id=artigo_null_id, titulo="Artigo null", tags=None, notas=None)
artigo_recuperado2 = Artigo.get(id=artigo_null_id)
print(f"Artigo com set/map nulos: {artigo_recuperado2}")
assert artigo_recuperado2.tags == set()
assert artigo_recuperado2.notas == {}
print("✅ Casos especiais de set/map funcionam!")

# 6. Testando Map com tipos diferentes
print("\n--- Testando Map com tipos diferentes ---")
class Config(Model):
    __table_name__ = "configs"
    id: fields.UUID = fields.UUID(primary_key=True)
    parametros: fields.Map = fields.Map(fields.Text(), fields.Text())

Config.sync_table()
config_id = uuid.uuid4()
parametros = {"env": "prod", "debug": "false"}
config = Config.create(id=config_id, parametros=parametros)
print(f"Config criada: {config}")
config_buscada = Config.get(id=config_id)
print(f"Config buscada: {config_buscada}")
assert config_buscada.parametros == parametros
print("✅ Map de texto funcionando!")

# 7. Desconectar
connection.disconnect()
print("\n🎉 Todos os testes de coleções passaram com sucesso!") 