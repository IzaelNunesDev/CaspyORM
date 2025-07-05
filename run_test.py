# run_test.py (REVISADO PARA TESTAR auto_apply)
import uuid
from caspyorm import fields, Model, connection
from datetime import datetime

# 1. Conectar ao Cassandra e limpar o ambiente para um teste limpo
connection.connect(contact_points=['127.0.0.1'], keyspace='caspyorm_test_sync')
session = connection.get_session()
session.execute("DROP TABLE IF EXISTS produtos")
print("Ambiente de teste limpo.")

# --- CENÁRIO 1: Criação inicial ---
print("\n--- CENÁRIO 1: Criação inicial da tabela ---")
class ProdutoV1(Model):
    __table_name__ = 'produtos'
    id: fields.UUID = fields.UUID(primary_key=True)
    nome: fields.Text = fields.Text(required=True)
    preco: fields.Float = fields.Float()

ProdutoV1.sync_table()

# --- CENÁRIO 2: Evolução do modelo com auto_apply=True ---
print("\n--- CENÁRIO 2: Sincronizando modelo evoluído com auto_apply=True ---")
class ProdutoV2(Model):
    __table_name__ = 'produtos'
    id: fields.UUID = fields.UUID(primary_key=True)
    nome: fields.Text = fields.Text(required=True)
    # CAMPO REMOVIDO: preco
    estoque: fields.Integer = fields.Integer(default=0) # CAMPO ADICIONADO
    ultima_atualizacao: fields.Timestamp = fields.Timestamp() # CAMPO ADICIONADO

# Sincroniza o modelo V2 com auto_apply=True
ProdutoV2.sync_table(auto_apply=True, verbose=True)

# --- Verificação ---
print("\n--- Verificando o schema final da tabela no DB ---")
db_schema_final = connection.get_cluster().metadata.keyspaces['caspyorm_test_sync'].tables['produtos']
final_columns = [col.name for col in db_schema_final.columns.values()]
print(f"Colunas na tabela 'produtos' após a sincronização: {final_columns}")

assert 'estoque' in final_columns
assert 'ultima_atualizacao' in final_columns
assert 'preco' in final_columns # 'preco' ainda deve existir, pois não removemos automaticamente

print("\n✅ Teste de AutoSchemaSync com auto_apply concluído com sucesso!")

connection.disconnect() 