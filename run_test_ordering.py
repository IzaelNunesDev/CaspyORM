# run_test_ordering.py

import uuid
from caspyorm import fields, Model, connection
from datetime import datetime, timedelta

# 1. Conexão e limpeza
connection.connect(contact_points=['127.0.0.1'], keyspace='caspyorm_order_test')
session = connection.get_session()
session.execute("DROP TABLE IF EXISTS medicoes_sensores")

# 2. Modelo com Chave Composta (Partition + Clustering)
# Vamos medir a temperatura de vários sensores ao longo do tempo.
class Medicao(Model):
    __table_name__ = "medicoes_sensores"
    
    # Chave de Partição: agrupa todas as medições de um sensor juntos
    sensor_id: fields.UUID = fields.UUID(partition_key=True)
    
    # Chave de Clusterização: ordena as medições dentro de uma partição por data
    # Isso é o que nos permite usar ORDER BY!
    registrado_em: fields.Timestamp = fields.Timestamp(clustering_key=True)
    
    temperatura: fields.Float = fields.Float()

Medicao.sync_table()
print("Modelo Medicao sincronizado.")

# 3. Inserir dados de teste (fora de ordem)
print("\n--- Inserindo dados de teste ---")
sensor_a = uuid.uuid4()
now = datetime.utcnow()

Medicao.create(sensor_id=sensor_a, registrado_em=now - timedelta(hours=2), temperatura=25.5)
Medicao.create(sensor_id=sensor_a, registrado_em=now, temperatura=28.0)
Medicao.create(sensor_id=sensor_a, registrado_em=now - timedelta(hours=1), temperatura=26.8)
Medicao.create(sensor_id=sensor_a, registrado_em=now - timedelta(minutes=30), temperatura=27.5)

# 4. Testando a ordenação
print(f"\n--- Buscando medições para o sensor {sensor_a} ---")

# Teste 1: Ordem padrão (ASCENDENTE por 'registrado_em')
print("\n[Ordenação] Padrão (ASC):")
medicoes_asc = Medicao.filter(sensor_id=sensor_a).all()
for m in medicoes_asc:
    print(f"  - {m.registrado_em.strftime('%H:%M:%S')} -> {m.temperatura}°C")

temperaturas_asc = [m.temperatura for m in medicoes_asc]
assert [round(t, 1) for t in temperaturas_asc] == [25.5, 26.8, 27.5, 28.0]
print("✅ Ordem ascendente correta!")

# Teste 2: Ordem descendente
print("\n[Ordenação] Descendente ('-registrado_em'):")
medicoes_desc = Medicao.filter(sensor_id=sensor_a).order_by('-registrado_em').all()
for m in medicoes_desc:
    print(f"  - {m.registrado_em.strftime('%H:%M:%S')} -> {m.temperatura}°C")

temperaturas_desc = [m.temperatura for m in medicoes_desc]
assert [round(t, 1) for t in temperaturas_desc] == [28.0, 27.5, 26.8, 25.5]
print("✅ Ordem descendente correta!")

# 5. Testando encadeamento com ordenação
print("\n--- Testando encadeamento com ordenação ---")

# Encadeamento: filtro + ordenação + limite
print("\n[Encadeamento] Filtro + Ordenação + Limite:")
medicoes_limitadas = Medicao.filter(sensor_id=sensor_a).order_by('-registrado_em').limit(2).all()
for m in medicoes_limitadas:
    print(f"  - {m.registrado_em.strftime('%H:%M:%S')} -> {m.temperatura}°C")

assert len(medicoes_limitadas) == 2
assert medicoes_limitadas[0].temperatura == 28.0  # Mais recente
print("✅ Encadeamento com ordenação funcionando!")

# 6. Testando múltiplos campos de ordenação
print("\n--- Testando múltiplos campos de ordenação ---")

# Adicionar mais dados com temperaturas iguais para testar ordenação secundária
Medicao.create(sensor_id=sensor_a, registrado_em=now - timedelta(minutes=15), temperatura=28.0)
Medicao.create(sensor_id=sensor_a, registrado_em=now - timedelta(minutes=45), temperatura=28.0)

print("\n[Ordenação] Múltiplos campos (temperatura DESC, registrado_em ASC):")
medicoes_multi = Medicao.filter(sensor_id=sensor_a).order_by('-temperatura', 'registrado_em').all()
for m in medicoes_multi:
    print(f"  - {m.registrado_em.strftime('%H:%M:%S')} -> {m.temperatura}°C")

# Verificar que as temperaturas 28.0 aparecem em ordem cronológica
temp_28_times = [m.registrado_em for m in medicoes_multi if m.temperatura == 28.0]
assert temp_28_times == sorted(temp_28_times)
print("✅ Ordenação múltipla funcionando!")

# 7. Testando QuerySet lazy com ordenação
print("\n--- Testando Lazy Evaluation com ordenação ---")

# Criar QuerySet sem executar
qs_ordenado = Medicao.filter(sensor_id=sensor_a).order_by('-registrado_em')
print(f"QuerySet criado: {qs_ordenado}")

# Executar ao iterar
print("\nExecutando query ordenada:")
for m in qs_ordenado:
    print(f"  - {m.registrado_em.strftime('%H:%M:%S')} -> {m.temperatura}°C")

# 8. Desconectar
connection.disconnect()
print("\n✅ Testes de ordenação concluídos com sucesso!") 