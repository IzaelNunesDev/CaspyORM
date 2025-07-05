"""
Testes para as melhorias do Nível 3 da CaspyORM: Criação de Índices Secundários.
"""
import pytest
import uuid
from caspyorm import Model, fields, connection

class ProdutoComIndice(Model):
    __table_name__ = 'produtos_com_indice_teste'
    id = fields.UUID(primary_key=True)
    nome = fields.Text(required=True)
    categoria = fields.Text(index=True)  # Campo que deve ser indexado
    preco = fields.Float(index=True)     # Outro campo indexado
    ativo = fields.Boolean()             # Campo não indexado

class ItemSemDefault(Model):
    __table_name__ = 'item_sem_default_teste'
    id = fields.UUID(primary_key=True, default=None)  # Explicitamente sem default para permitir a instanciação com None
    nome = fields.Text()

class Post(Model):
    __table_name__ = 'posts_collection_update'
    id = fields.UUID(primary_key=True)
    tags = fields.List(fields.Text())
    colaboradores = fields.Set(fields.Text())

@pytest.fixture(autouse=True)
def limpar_tabela_indice(session):
    """Limpa a tabela antes de cada teste."""
    session.execute(f"DROP TABLE IF EXISTS {ProdutoComIndice.__table_name__}")
    yield

def test_sync_table_cria_indice_secundario(session):
    """Testa se o sync_table cria corretamente um índice secundário."""
    # Sincroniza a tabela. A lógica modificada deve criar a tabela E o índice.
    ProdutoComIndice.sync_table()

    # Verifica se os índices foram realmente criados no schema do Cassandra
    keyspace = session.keyspace
    index_names = [
        f"{ProdutoComIndice.__table_name__}_categoria_idx",
        f"{ProdutoComIndice.__table_name__}_preco_idx"
    ]
    
    for index_name in index_names:
        query = f"""
            SELECT index_name FROM system_schema.indexes
            WHERE keyspace_name = '{keyspace}'
            AND table_name = '{ProdutoComIndice.__table_name__}'
            AND index_name = '{index_name}'
        """
        
        result = session.execute(query)
        assert result.one() is not None, f"O índice '{index_name}' não foi encontrado no schema."

def test_sync_table_nao_cria_indice_para_campo_nao_indexado(session):
    """Testa se o sync_table NÃO cria índice para campos sem index=True."""
    ProdutoComIndice.sync_table()

    # Verifica que NÃO há índice para o campo 'ativo' (não indexado)
    keyspace = session.keyspace
    index_name = f"{ProdutoComIndice.__table_name__}_ativo_idx"
    
    query = f"""
        SELECT index_name FROM system_schema.indexes
        WHERE keyspace_name = '{keyspace}'
        AND table_name = '{ProdutoComIndice.__table_name__}'
        AND index_name = '{index_name}'
    """
    
    result = session.execute(query)
    assert result.one() is None, f"O índice '{index_name}' foi criado indevidamente."

def test_sync_table_nao_falha_se_indice_ja_existe(session):
    """Testa se o sync_table não falha quando o índice já existe."""
    # Primeira sincronização
    ProdutoComIndice.sync_table()
    
    # Segunda sincronização (deve detectar que os índices já existem)
    ProdutoComIndice.sync_table()
    
    # Se chegou até aqui sem erro, o teste passou
    assert True

def test_filtro_com_campo_indexado_nao_gera_warning(session):
    """Testa se filtro em campo indexado não gera warning."""
    import warnings
    
    ProdutoComIndice.sync_table()
    
    # Criar um produto para testar
    produto = ProdutoComIndice.create(
        id=uuid.uuid4(),
        nome="Produto Teste",
        categoria="Eletrônicos",
        preco=99.99
    )
    
    # Filtro em campo indexado não deve gerar warning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        resultados = list(ProdutoComIndice.filter(categoria="Eletrônicos"))
        
        # Verificar que não há warnings sobre campo não indexado
        for warning in w:
            assert "não é uma chave primária nem está indexado" not in str(warning.message)
    
    assert len(resultados) == 1
    assert resultados[0].id == produto.id

def test_filtro_com_campo_nao_indexado_gera_warning(session):
    """Testa se filtro em campo não indexado gera warning."""
    import warnings
    
    ProdutoComIndice.sync_table()
    
    # Criar um produto para testar
    ProdutoComIndice.create(
        id=uuid.uuid4(),
        nome="Produto Teste",
        categoria="Eletrônicos",
        preco=99.99,
        ativo=True
    )
    
    # Filtro em campo não indexado deve gerar warning
    with pytest.warns(UserWarning, match="não é uma chave primária nem está indexado"):
        list(ProdutoComIndice.filter(ativo=True))

def test_optimized_count_method(session):
    """Testa se o método count() otimizado funciona corretamente."""
    ProdutoComIndice.sync_table()
    
    # Criar dados de teste
    for i in range(5):  # 5 eletrônicos
        ProdutoComIndice.create(
            id=uuid.uuid4(),
            nome=f"Produto Eletro {i}",
            categoria="eletronicos",
            preco=100.0 + i
        )
    
    for i in range(3):  # 3 livros
        ProdutoComIndice.create(
            id=uuid.uuid4(),
            nome=f"Produto Livro {i}",
            categoria="livros",
            preco=50.0 + i
        )
        
    # Testar contagem total
    total_count = ProdutoComIndice.all().count()
    assert total_count == 8, f"Esperado 8 produtos, mas count() retornou {total_count}"
    
    # Testar contagem com filtro
    eletronicos_count = ProdutoComIndice.filter(categoria="eletronicos").count()
    assert eletronicos_count == 5, f"Esperado 5 eletrônicos, mas count() retornou {eletronicos_count}"
    
    livros_count = ProdutoComIndice.filter(categoria="livros").count()
    assert livros_count == 3, f"Esperado 3 livros, mas count() retornou {livros_count}"
    
    # Testar contagem com filtro sem resultados
    inexistente_count = ProdutoComIndice.filter(categoria="inexistente").count()
    assert inexistente_count == 0, f"Esperado 0 resultados, mas count() retornou {inexistente_count}"

def test_count_method_with_complex_filters(session):
    """Testa se o método count() funciona com filtros complexos."""
    ProdutoComIndice.sync_table()
    
    # Criar produtos com preços diferentes
    for i in range(10):
        ProdutoComIndice.create(
            id=uuid.uuid4(),
            nome=f"Produto {i}",
            categoria="teste",
            preco=float(i * 10)
        )
    
    # Testar filtros com operadores
    produtos_caros = ProdutoComIndice.filter(preco__gte=50.0).count()
    assert produtos_caros == 5, f"Esperado 5 produtos com preço >= 50, mas count() retornou {produtos_caros}"
    
    produtos_baratos = ProdutoComIndice.filter(preco__lt=30.0).count()
    assert produtos_baratos == 3, f"Esperado 3 produtos com preço < 30, mas count() retornou {produtos_baratos}"
    
    # Testar filtro IN
    produtos_especificos = ProdutoComIndice.filter(preco__in=[0.0, 20.0, 40.0]).count()
    assert produtos_especificos == 3, f"Esperado 3 produtos com preços específicos, mas count() retornou {produtos_especificos}"

def test_optimized_exists_method(session):
    """Testa se o método exists() otimizado funciona corretamente."""
    ProdutoComIndice.sync_table()

    # Cria um dado de teste
    ProdutoComIndice.create(
        id=uuid.uuid4(),
        nome="Produto para Teste de Existência", 
        categoria="existente",
        preco=99.99
    )

    # 1. Testa o caso onde o registro EXISTE
    qs_exists = ProdutoComIndice.filter(categoria="existente")
    assert qs_exists.exists() is True, "exists() deveria retornar True para um registro que existe."

    # 2. Testa o caso onde o registro NÃO EXISTE
    qs_not_exists = ProdutoComIndice.filter(categoria="nao_existe")
    assert qs_not_exists.exists() is False, "exists() deveria retornar False para um registro que não existe."

    # 3. Testa se o cache é utilizado corretamente
    # Primeiro, executa uma query para popular o cache
    list(qs_exists) 
    # Agora, o .exists() deve usar o cache e não executar uma nova query
    assert qs_exists.exists() is True, "exists() deveria funcionar com um queryset já populado."

    # 4. Testa um queryset que foi populado e resultou em vazio
    results = list(qs_not_exists)
    assert not results  # Garante que a lista está vazia
    assert qs_not_exists.exists() is False, "exists() deveria funcionar com um queryset vazio já populado."

def test_exists_method_with_complex_filters(session):
    """Testa se o método exists() funciona com filtros complexos."""
    ProdutoComIndice.sync_table()
    
    # Criar produtos com preços diferentes
    for i in range(5):
        ProdutoComIndice.create(
            id=uuid.uuid4(),
            nome=f"Produto {i}",
            categoria="teste_exists",
            preco=float(i * 10)
        )
    
    # Testar filtros com operadores
    produtos_caros_existem = ProdutoComIndice.filter(preco__gte=30.0).exists()
    assert produtos_caros_existem is True, "exists() deveria retornar True para produtos com preço >= 30"
    
    produtos_muito_caros_existem = ProdutoComIndice.filter(preco__gt=100.0).exists()
    assert produtos_muito_caros_existem is False, "exists() deveria retornar False para produtos com preço > 100"
    
    # Testar filtro IN
    produtos_especificos_existem = ProdutoComIndice.filter(preco__in=[0.0, 20.0]).exists()
    assert produtos_especificos_existem is True, "exists() deveria retornar True para produtos com preços específicos"

def test_bulk_create_operation(session):
    """Testa a operação bulk_create para inserção em lote."""
    ProdutoComIndice.sync_table()

    # Gera uma lista de instâncias para criar
    num_instances = 5
    instances_to_create = []
    for i in range(num_instances):
        # Importante: instanciamos primeiro, não salvamos
        p = ProdutoComIndice(
            id=uuid.uuid4(),
            nome=f"Produto em Lote {i}",
            categoria="lote",
            preco=float(i * 10)
        )
        instances_to_create.append(p)

    # Executa a criação em lote
    created_instances = ProdutoComIndice.bulk_create(instances_to_create)

    assert len(created_instances) == num_instances

    # Verifica se todos os produtos foram realmente criados no banco
    count = ProdutoComIndice.filter(categoria="lote").count()
    assert count == num_instances, "A contagem de produtos criados em lote no banco de dados está incorreta."

    # Verifica se um dos produtos existe
    first_id = created_instances[0].id
    p_from_db = ProdutoComIndice.get(id=first_id)
    assert p_from_db is not None
    assert p_from_db.nome == "Produto em Lote 0"
    assert p_from_db.preco == 0.0

def test_bulk_create_with_pk_null_fails(session):
    """Testa se bulk_create falha se uma chave primária for nula, validando a exceção correta."""
    ItemSemDefault.sync_table()

    # Este modelo permite a criação de uma instância com id=None
    instancia_invalida = ItemSemDefault(id=None, nome="Produto Inválido")
    
    # A exceção ValueError deve ser levantada pela validação interna do bulk_create
    with pytest.raises(ValueError, match="Primary key 'id' não pode ser nula em bulk_create"):
        ItemSemDefault.bulk_create([instancia_invalida])

def test_bulk_create_empty_list(session):
    """Testa se bulk_create funciona corretamente com lista vazia."""
    ProdutoComIndice.sync_table()

    result = ProdutoComIndice.bulk_create([])
    assert result == [], "bulk_create com lista vazia deve retornar lista vazia"

def test_bulk_create_large_batch(session):
    """Testa se bulk_create funciona com lotes grandes (testa o limite de 100)."""
    ProdutoComIndice.sync_table()

    # Criar 150 instâncias para testar o limite de batch
    num_instances = 150
    instances_to_create = []
    for i in range(num_instances):
        p = ProdutoComIndice(
            id=uuid.uuid4(),
            nome=f"Produto Grande Lote {i}",
            categoria="grande_lote",
            preco=float(i)
        )
        instances_to_create.append(p)

    # Executa a criação em lote
    created_instances = ProdutoComIndice.bulk_create(instances_to_create)

    assert len(created_instances) == num_instances

    # Verifica se todos foram criados
    count = ProdutoComIndice.filter(categoria="grande_lote").count()
    assert count == num_instances, f"Esperado {num_instances} produtos, mas encontrado {count}"

def test_atomic_collection_update(session):
    """Testa a atualização atômica de coleções (List e Set)."""
    Post.sync_table()

    # Cria um post inicial
    post = Post.create(
        id=uuid.uuid4(),
        tags=['python', 'orm'],
        colaboradores={'ana', 'bruno'}
    )

    # 1. Adicionar itens a uma lista
    post.update_collection('tags', add=['cassandra'])
    
    # 2. Remover itens de um set
    post.update_collection('colaboradores', remove={'bruno'})

    # Busca o post do banco para verificar o estado final
    updated_post = Post.get(id=post.id)
    
    assert sorted(updated_post.tags) == sorted(['python', 'orm', 'cassandra'])
    assert updated_post.colaboradores == {'ana'} 