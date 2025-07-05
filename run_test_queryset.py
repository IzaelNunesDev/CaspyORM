# run_test_queryset.py

import uuid
from caspyorm import fields, Model, connection

# 1. Conectar e limpar o ambiente
connection.connect(contact_points=['127.0.0.1'], keyspace='caspyorm_qs_test')
session = connection.get_session()
session.execute("DROP TABLE IF EXISTS funcionarios")

# 2. Definir e sincronizar o modelo
class Funcionario(Model):
    id: fields.UUID = fields.UUID(primary_key=True)
    nome: fields.Text = fields.Text(required=True)
    setor: fields.Text = fields.Text(index=True)
    salario: fields.Integer = fields.Integer()

Funcionario.sync_table()
print("Modelo Funcionario sincronizado.")

# 3. Inserir dados de teste
print("\n--- Inserindo dados de teste ---")
Funcionario.create(id=uuid.uuid4(), nome="Ana", setor="Engenharia", salario=7000)
Funcionario.create(id=uuid.uuid4(), nome="Bruno", setor="Engenharia", salario=8000)
Funcionario.create(id=uuid.uuid4(), nome="Carla", setor="Marketing", salario=6000)
Funcionario.create(id=uuid.uuid4(), nome="Daniel", setor="Engenharia", salario=9000)

# 4. Testando QuerySet - Lazy Evaluation
print("\n--- Testando Lazy Evaluation ---")
qs_engenharia = Funcionario.filter(setor="Engenharia")
print(f"QuerySet criado, mas não executado: {qs_engenharia}") # Deve mostrar <QuerySet ...>

# 5. Executando a query ao iterar
print("\n--- Executando a query ao iterar ---")
for func in qs_engenharia:
    print(f"  - Funcionário encontrado: {func.nome}, Salário: {func.salario}")

# 6. Testando encadeamento com .limit()
print("\n--- Testando encadeamento com .limit(2) ---")
engenheiros_limitados = Funcionario.filter(setor="Engenharia").limit(2)
print(f"QuerySet com limite: {engenheiros_limitados}")
resultados = engenheiros_limitados.all() # .all() força a execução
print(f"Encontrados {len(resultados)} engenheiros.")
for func in resultados:
    print(f"  - {func.nome}")

# 7. Testando .first()
print("\n--- Testando .first() ---")
primeiro_marketing = Funcionario.filter(setor="Marketing").first()
print(f"Primeiro funcionário do Marketing: {primeiro_marketing}")
if primeiro_marketing:
    assert primeiro_marketing.nome == "Carla"

primeiro_qualquer = Funcionario.all().first()
print(f"Primeiro funcionário qualquer: {primeiro_qualquer}")

# 8. Testando .count()
print("\n--- Testando .count() ---")
total_engenheiros = Funcionario.filter(setor="Engenharia").count()
print(f"Total de funcionários na Engenharia: {total_engenheiros}")
assert total_engenheiros == 3

# 9. Testando múltiplos filtros
print("\n--- Testando múltiplos filtros ---")
engenheiros_ricos = Funcionario.filter(setor="Engenharia").filter(salario=9000)
print(f"QuerySet com múltiplos filtros: {engenheiros_ricos}")
for func in engenheiros_ricos:
    print(f"  - {func.nome} (R$ {func.salario})")

# 10. Testando QuerySet vazio
print("\n--- Testando QuerySet vazio ---")
funcionarios_inexistentes = Funcionario.filter(setor="Inexistente")
print(f"QuerySet para setor inexistente: {funcionarios_inexistentes}")
resultados_vazios = list(funcionarios_inexistentes)
print(f"Resultados encontrados: {len(resultados_vazios)}")

print("\n✅ Teste do QuerySet concluído com sucesso!")

connection.disconnect() 