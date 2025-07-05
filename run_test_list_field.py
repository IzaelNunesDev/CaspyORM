# run_test_list_field.py

import uuid
from caspyorm import fields, Model, connection

# 1. Conexão e limpeza
connection.connect(contact_points=['127.0.0.1'], keyspace='caspyorm_list_test')
session = connection.get_session()
session.execute("DROP TABLE IF EXISTS posts")

# 2. Modelo com um campo de lista e sincronização
class Post(Model):
    __table_name__ = "posts"
    id: fields.UUID = fields.UUID(primary_key=True)
    titulo: fields.Text = fields.Text(required=True)
    tags: fields.List = fields.List(fields.Text())  # Uma lista de textos
    upvotes: fields.Integer = fields.Integer(default=0)

Post.sync_table()
print("Modelo Post sincronizado.")
print("Schema interno do Post:", Post.__caspy_schema__)

# 3. Inserir dados com uma lista
print("\n--- Inserindo um post com tags ---")
post_id = uuid.uuid4()
tags_para_post = ["python", "cassandra", "orm"]

post_novo = Post.create(
    id=post_id,
    titulo="Introdução à CaspyORM",
    tags=tags_para_post
)
print(f"Post criado: {post_novo}")
assert post_novo.tags == tags_para_post

# 4. Buscar e verificar o campo de lista
print("\n--- Buscando o post e verificando as tags ---")
post_buscado = Post.get(id=post_id)
print(f"Post buscado: {post_buscado}")

assert post_buscado is not None
assert isinstance(post_buscado.tags, list)
assert post_buscado.tags == tags_para_post
print("✅ O campo de lista foi salvo e recuperado corretamente!")

# 5. Testando com lista vazia e None
print("\n--- Testando casos especiais ---")
post_sem_tags_id = uuid.uuid4()
Post.create(id=post_sem_tags_id, titulo="Post sem tags", tags=[])  # Lista vazia
post_recuperado1 = Post.get(id=post_sem_tags_id)
print(f"Post com lista vazia: {post_recuperado1}")
assert post_recuperado1.tags == []

post_null_tags_id = uuid.uuid4()
Post.create(id=post_null_tags_id, titulo="Post com tags nulas", tags=None)  # Valor None
post_recuperado2 = Post.get(id=post_null_tags_id)
print(f"Post com tags nulas: {post_recuperado2}")
# Nossa implementação de to_python converte None para lista vazia
assert post_recuperado2.tags == [] 
print("✅ Casos especiais de lista funcionam!")

# 6. Testando lista de inteiros
print("\n--- Testando lista de inteiros ---")
class Produto(Model):
    __table_name__ = "produtos"
    id: fields.UUID = fields.UUID(primary_key=True)
    nome: fields.Text = fields.Text(required=True)
    precos: fields.List = fields.List(fields.Integer())  # Lista de inteiros
    categorias: fields.List = fields.List(fields.Text())

session.execute("DROP TABLE IF EXISTS produtos")
Produto.sync_table()

produto_id = uuid.uuid4()
precos = [100, 200, 300]
categorias = ["eletronicos", "computadores"]

produto = Produto.create(
    id=produto_id,
    nome="Laptop Gaming",
    precos=precos,
    categorias=categorias
)
print(f"Produto criado: {produto}")

produto_buscado = Produto.get(id=produto_id)
print(f"Produto buscado: {produto_buscado}")
assert produto_buscado.precos == precos
assert produto_buscado.categorias == categorias
print("✅ Lista de inteiros funcionando!")

# 7. Desconectar
connection.disconnect()
print("\n🎉 Todos os testes de lista passaram com sucesso!") 