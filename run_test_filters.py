# run_test_filters.py

import uuid
from caspyorm import fields, Model, connection

# 1. Conexão e limpeza
connection.connect(contact_points=['127.0.0.1'], keyspace='caspyorm_filter_test')
session = connection.get_session()
session.execute("DROP TABLE IF EXISTS funcionarios_filters")

# 2. Modelo e Sincronização
class Funcionario(Model):
    __table_name__ = "funcionarios_filters"
    id: fields.UUID = fields.UUID(primary_key=True)
    nome: fields.Text = fields.Text(required=True)
    setor: fields.Text = fields.Text(index=True)
    salario: fields.Integer = fields.Integer()

Funcionario.sync_table()
print("Modelo Funcionario (filters) sincronizado.")

# 3. Inserir dados
print("\n--- Inserindo dados ---")
Funcionario.create(id=uuid.uuid4(), nome="Ana", setor="Engenharia", salario=7000)
Funcionario.create(id=uuid.uuid4(), nome="Bruno", setor="Engenharia", salario=8000)
Funcionario.create(id=uuid.uuid4(), nome="Carla", setor="Marketing", salario=6000)
Funcionario.create(id=uuid.uuid4(), nome="Daniel", setor="Engenharia", salario=9500)
Funcionario.create(id=uuid.uuid4(), nome="Elisa", setor="RH", salario=7000)

# 4. Testando filtros avançados
print("\n--- Testando filtros avançados ---")

# Maior que (>)
print("\n[Filtro] Salário > 7500:")
altos_salarios = Funcionario.filter(salario__gt=7500).all()
for f in altos_salarios:
    print(f"  - {f.nome} (Salário: {f.salario})")
assert len(altos_salarios) == 2

# Menor ou igual que (<=)
print("\n[Filtro] Salário <= 7000:")
salarios_base = Funcionario.filter(salario__lte=7000).all()
for f in salarios_base:
    print(f"  - {f.nome} (Salário: {f.salario})")
assert len(salarios_base) == 3

# IN
print("\n[Filtro] Setor IN ('Marketing', 'RH'):")
mkt_rh = Funcionario.filter(setor__in=['Marketing', 'RH']).all()
for f in mkt_rh:
    print(f"  - {f.nome} (Setor: {f.setor})")
assert len(mkt_rh) == 2

# Combinação de filtros
print("\n[Filtro] Setor 'Engenharia' E Salário > 8000:")
engenheiro_senior = Funcionario.filter(setor='Engenharia', salario__gt=8000).first()
if engenheiro_senior:
    print(f"  - {engenheiro_senior.nome} (Salário: {engenheiro_senior.salario})")
    assert engenheiro_senior.nome == "Daniel"

# 5. Testando outros operadores
print("\n--- Testando outros operadores ---")

# Maior ou igual que (>=)
print("\n[Filtro] Salário >= 8000:")
salarios_altos = Funcionario.filter(salario__gte=8000).all()
for f in salarios_altos:
    print(f"  - {f.nome} (Salário: {f.salario})")
assert len(salarios_altos) == 2

# Menor que (<)
print("\n[Filtro] Salário < 7500:")
salarios_baixos = Funcionario.filter(salario__lt=7500).all()
for f in salarios_baixos:
    print(f"  - {f.nome} (Salário: {f.salario})")
assert len(salarios_baixos) == 3

# Igualdade explícita (__exact)
print("\n[Filtro] Salário = 7000 (explicitamente):")
salario_exato = Funcionario.filter(salario__exact=7000).all()
for f in salario_exato:
    print(f"  - {f.nome} (Salário: {f.salario})")
assert len(salario_exato) == 2

# 6. Testando encadeamento com operadores
print("\n--- Testando encadeamento com operadores ---")

# Encadeamento: setor + salário + limite
engenheiros_ricos = Funcionario.filter(setor='Engenharia').filter(salario__gt=7500).limit(2)
print("\n[Encadeamento] Engenheiros com salário > 7500 (limit 2):")
for f in engenheiros_ricos:
    print(f"  - {f.nome} (Salário: {f.salario})")

# 7. Testando operador IN com diferentes tipos
print("\n--- Testando operador IN ---")

# IN com salários
print("\n[Filtro] Salário IN (6000, 7000):")
salarios_especificos = Funcionario.filter(salario__in=[6000, 7000]).all()
for f in salarios_especificos:
    print(f"  - {f.nome} (Salário: {f.salario})")
assert len(salarios_especificos) == 3

# 8. Testando filtros vazios
print("\n--- Testando filtros vazios ---")

# Filtro que não retorna resultados
sem_resultados = Funcionario.filter(salario__gt=10000).all()
print(f"\n[Filtro] Salário > 10000: {len(sem_resultados)} resultados")
assert len(sem_resultados) == 0

# 9. Testando filtros combinados complexos
print("\n--- Testando filtros complexos ---")

# Múltiplos filtros em uma só chamada
filtros_complexos = Funcionario.filter(
    setor__in=['Engenharia', 'Marketing'],
    salario__gte=7000
).all()

print("\n[Filtro Complexo] Setor IN ('Engenharia', 'Marketing') AND Salário >= 7000:")
for f in filtros_complexos:
    print(f"  - {f.nome} ({f.setor}, R$ {f.salario})")
assert len(filtros_complexos) == 3

# 10. Desconectar
connection.disconnect()
print("\n✅ Testes de filtros avançados concluídos com sucesso!") 