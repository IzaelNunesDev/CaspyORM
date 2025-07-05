# test_queryset_advanced.py

import uuid
from caspyorm import fields, Model, connection

# 1. Conectar e preparar ambiente
connection.connect(contact_points=['127.0.0.1'], keyspace='caspyorm_advanced_test')
session = connection.get_session()
session.execute("DROP TABLE IF EXISTS produtos")

# 2. Definir modelo mais complexo
class Produto(Model):
    id: fields.UUID = fields.UUID(primary_key=True)
    nome: fields.Text = fields.Text(required=True)
    categoria: fields.Text = fields.Text(index=True)
    preco: fields.Float = fields.Float()
    estoque: fields.Integer = fields.Integer()
    ativo: fields.Boolean = fields.Boolean(default=True)

Produto.sync_table()
print("Modelo Produto sincronizado.")

# 3. Inserir dados de teste
print("\n--- Inserindo produtos de teste ---")
produtos_teste = [
    {"nome": "Laptop Dell", "categoria": "Eletrônicos", "preco": 3500.0, "estoque": 10, "ativo": True},
    {"nome": "Mouse Wireless", "categoria": "Eletrônicos", "preco": 89.90, "estoque": 50, "ativo": True},
    {"nome": "Teclado Mecânico", "categoria": "Eletrônicos", "preco": 299.90, "estoque": 25, "ativo": True},
    {"nome": "Livro Python", "categoria": "Livros", "preco": 89.90, "estoque": 15, "ativo": True},
    {"nome": "Livro Cassandra", "categoria": "Livros", "preco": 120.0, "estoque": 8, "ativo": True},
    {"nome": "Café Especial", "categoria": "Alimentos", "preco": 45.90, "estoque": 100, "ativo": True},
    {"nome": "Produto Inativo", "categoria": "Teste", "preco": 10.0, "estoque": 0, "ativo": False},
]

for produto_data in produtos_teste:
    Produto.create(id=uuid.uuid4(), **produto_data)

print(f"Inseridos {len(produtos_teste)} produtos.")

# 4. Demonstração de Lazy Evaluation
print("\n=== DEMONSTRAÇÃO DE LAZY EVALUATION ===")
print("Criando QuerySets sem executar queries...")

# QuerySet 1 - Produtos eletrônicos
qs_eletronicos = Produto.filter(categoria="Eletrônicos")
print(f"QuerySet 1: {qs_eletronicos}")

# QuerySet 2 - Produtos com estoque baixo
qs_estoque_baixo = Produto.filter(estoque=0)
print(f"QuerySet 2: {qs_estoque_baixo}")

# QuerySet 3 - Produtos ativos
qs_ativos = Produto.filter(ativo=True)
print(f"QuerySet 3: {qs_ativos}")

print("\nAgora executando as queries...")

# 5. Executando queries e mostrando resultados
print("\n--- Resultados dos QuerySets ---")

print("\nProdutos Eletrônicos:")
for produto in qs_eletronicos:
    print(f"  - {produto.nome}: R$ {produto.preco:.2f} (Estoque: {produto.estoque})")

print("\nProdutos com Estoque Zero:")
for produto in qs_estoque_baixo:
    print(f"  - {produto.nome} ({produto.categoria})")

print("\nProdutos Ativos:")
ativos_lista = list(qs_ativos)
print(f"Total de produtos ativos: {len(ativos_lista)}")

# 6. Demonstração de Encadeamento
print("\n=== DEMONSTRAÇÃO DE ENCADEAMENTO ===")

# Encadeamento: eletrônicos + limite de 2
print("\n--- Eletrônicos limitados a 2 ---")
eletronicos_limitados = Produto.filter(categoria="Eletrônicos").limit(2)
print(f"QuerySet encadeado: {eletronicos_limitados}")
for produto in eletronicos_limitados:
    print(f"  - {produto.nome}")

# 7. Demonstração de Métodos Úteis
print("\n=== MÉTODOS ÚTEIS DO QUERYSET ===")

# .first() - Primeiro produto
primeiro_produto = Produto.all().first()
if primeiro_produto:
    print(f"\nPrimeiro produto: {primeiro_produto.nome}")
else:
    print("\nNenhum produto encontrado")

# .count() - Contagem
total_eletronicos = Produto.filter(categoria="Eletrônicos").count()
print(f"Total de produtos eletrônicos: {total_eletronicos}")

total_ativos = Produto.filter(ativo=True).count()
print(f"Total de produtos ativos: {total_ativos}")

# 8. Demonstração de Múltiplos Filtros
print("\n=== MÚLTIPLOS FILTROS ===")

# Produtos eletrônicos com estoque > 20
eletronicos_estoque_alto = Produto.filter(categoria="Eletrônicos").filter(estoque=50)
print("\nProdutos eletrônicos com estoque = 50:")
for produto in eletronicos_estoque_alto:
    print(f"  - {produto.nome} (Estoque: {produto.estoque})")

# 9. Demonstração de Conversão para Lista
print("\n=== CONVERSÃO PARA LISTA ===")
produtos_livros = list(Produto.filter(categoria="Livros"))
print(f"Produtos da categoria Livros (como lista): {len(produtos_livros)} itens")
for produto in produtos_livros:
    print(f"  - {produto.nome}: R$ {produto.preco:.2f}")

# 10. Demonstração de QuerySet Vazio
print("\n=== QUERYSET VAZIO ===")
produtos_inexistentes = Produto.filter(categoria="CategoriaInexistente")
print(f"QuerySet para categoria inexistente: {produtos_inexistentes}")
resultados_vazios = list(produtos_inexistentes)
print(f"Resultados encontrados: {len(resultados_vazios)}")

# 11. Demonstração de Performance
print("\n=== DEMONSTRAÇÃO DE PERFORMANCE ===")
print("Criando múltiplos QuerySets sem executar...")

querysets = []
for i in range(10):
    qs = Produto.filter(categoria="Eletrônicos").limit(i + 1)
    querysets.append(qs)
    print(f"QuerySet {i+1} criado: {qs}")

print("\nExecutando apenas o último QuerySet...")
resultado_final = list(querysets[-1])
print(f"Resultado final: {len(resultado_final)} produtos")

print("\n✅ Teste avançado do QuerySet concluído com sucesso!")

connection.disconnect() 