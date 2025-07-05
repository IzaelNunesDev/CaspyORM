# run_test_delete.py

import uuid
from caspyorm import fields, Model, connection

# 1. Conexão e limpeza
connection.connect(contact_points=['127.0.0.1'], keyspace='caspyorm_delete_test')
session = connection.get_session()
session.execute("DROP TABLE IF EXISTS tarefas")

# 2. Modelo e Sincronização
class Tarefa(Model):
    __table_name__ = "tarefas"
    id: fields.UUID = fields.UUID(primary_key=True)
    projeto: fields.Text = fields.Text(index=True)
    descricao: fields.Text = fields.Text(required=True)
    concluida: fields.Boolean = fields.Boolean(default=False)

Tarefa.sync_table()
print("Modelo Tarefa sincronizado.")

# 3. Inserir dados
print("\n--- Inserindo dados ---")
tarefa1_id = uuid.uuid4()
tarefa1 = Tarefa.create(id=tarefa1_id, projeto="CaspyORM", descricao="Implementar .delete()", concluida=False)

tarefa2_id = uuid.uuid4()
Tarefa.create(id=tarefa2_id, projeto="Outro Projeto", descricao="Revisar docs", concluida=True)

tarefa3_id = uuid.uuid4()
Tarefa.create(id=tarefa3_id, projeto="CaspyORM", descricao="Escrever testes", concluida=False)

# 4. Testando deleção de instância
print("\n--- Testando deleção de instância ---")
tarefa_a_deletar = Tarefa.get(id=tarefa1_id)
print(f"Tarefa a ser deletada: {tarefa_a_deletar}")
assert tarefa_a_deletar is not None

# Deleta a instância
tarefa_a_deletar.delete()

# Tenta buscar novamente
tarefa_deletada = Tarefa.get(id=tarefa1_id)
print(f"Resultado da busca após deleção: {tarefa_deletada}")
assert tarefa_deletada is None
print("✅ Deleção de instância funcionou!")

# 5. Testando deleção via QuerySet
# NOTA: No Cassandra, deletar por um campo não-PK requer `ALLOW FILTERING` e pode ser lento.
# Nossa implementação de segurança exige a chave de partição. Vamos simular um modelo diferente.

session.execute("DROP TABLE IF EXISTS logs")
class Log(Model):
    app_id: fields.Text = fields.Text(partition_key=True)
    evento_id: fields.UUID = fields.UUID(clustering_key=True)
    mensagem: fields.Text = fields.Text()

Log.sync_table()
log_app_id = "app-01"
Log.create(app_id=log_app_id, evento_id=uuid.uuid4(), mensagem="Usuário logado")
Log.create(app_id=log_app_id, evento_id=uuid.uuid4(), mensagem="Erro de pagamento")
Log.create(app_id="app-02", evento_id=uuid.uuid4(), mensagem="Outro log")

print("\n--- Testando deleção em massa via QuerySet ---")
# Deleta todos os logs do 'app-01'
logs_deletados_count = Log.filter(app_id=log_app_id).delete()
print(f"Operação de deleção em massa para '{log_app_id}' concluída.")

# Verifica se os logs foram removidos
logs_restantes = Log.filter(app_id=log_app_id).all()
print(f"Logs restantes para '{log_app_id}': {len(logs_restantes)}")
assert len(logs_restantes) == 0
print("✅ Deleção via QuerySet funcionou!")

# 6. Desconectar
connection.disconnect() 