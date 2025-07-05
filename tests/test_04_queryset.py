import uuid
import pytest
from caspyorm import fields, Model

class Funcionario(Model):
    __table_name__ = "funcionarios_qs"
    id = fields.UUID()
    setor = fields.Text(primary_key=True)
    salario = fields.Integer(clustering_key=True) # Importante para ordenação
    nome = fields.Text()

@pytest.fixture(scope="function")
def funcionarios_data(session):
    session.execute(f"DROP TABLE IF EXISTS {Funcionario.__table_name__}")
    Funcionario.sync_table()
    Funcionario.create(setor="Engenharia", salario=7000, nome="Ana", id=uuid.uuid4())
    Funcionario.create(setor="Engenharia", salario=9500, nome="Daniel", id=uuid.uuid4())
    Funcionario.create(setor="Marketing", salario=6000, nome="Carla", id=uuid.uuid4())
    return

def test_filter_gt(funcionarios_data):
    resultado = Funcionario.filter(setor="Engenharia", salario__gt=8000).all()
    assert len(resultado) == 1
    assert resultado[0].nome == "Daniel"

def test_filter_in(funcionarios_data):
    resultado = Funcionario.filter(setor__in=["Marketing", "Vendas"]).all()
    assert len(resultado) == 1
    assert resultado[0].nome == "Carla"

def test_order_by_desc(funcionarios_data):
    resultado = Funcionario.filter(setor="Engenharia").order_by("-salario").all()
    assert [f.salario for f in resultado] == [9500, 7000]

def test_lazy_evaluation(funcionarios_data, capsys):
    qs = Funcionario.filter(setor="Engenharia")
    # Nenhum print de "EXECUTADO" deve aparecer ainda
    captured = capsys.readouterr()
    assert "EXECUTADO" not in captured.out
    
    list(qs) # Força a execução
    captured = capsys.readouterr()
    assert "EXECUTADO" in captured.out

def test_filter_com_operadores(session):
    session.execute(f"DROP TABLE IF EXISTS {Funcionario.__table_name__}")
    Funcionario.sync_table()
    
    f1 = Funcionario.create(setor="TI", salario=5000, nome="João", id=uuid.uuid4())
    f2 = Funcionario.create(setor="TI", salario=8000, nome="Maria", id=uuid.uuid4())
    f3 = Funcionario.create(setor="RH", salario=6000, nome="Pedro", id=uuid.uuid4())
    
    # Teste __lt (menor que)
    resultado = Funcionario.filter(setor="TI", salario__lt=7000).all()
    assert len(resultado) == 1
    assert resultado[0].nome == "João"
    
    # Teste __gte (maior ou igual)
    resultado = Funcionario.filter(setor="TI", salario__gte=7000).all()
    assert len(resultado) == 1
    assert resultado[0].nome == "Maria"

def test_limit(session):
    session.execute(f"DROP TABLE IF EXISTS {Funcionario.__table_name__}")
    Funcionario.sync_table()
    
    for i in range(5):
        Funcionario.create(setor="Teste", salario=1000+i, nome=f"Func{i}", id=uuid.uuid4())
    
    resultado = Funcionario.filter(setor="Teste").limit(3).all()
    assert len(resultado) == 3

def test_first(session):
    session.execute(f"DROP TABLE IF EXISTS {Funcionario.__table_name__}")
    Funcionario.sync_table()
    
    Funcionario.create(setor="Teste", salario=1000, nome="Primeiro", id=uuid.uuid4())
    Funcionario.create(setor="Teste", salario=2000, nome="Segundo", id=uuid.uuid4())
    
    primeiro = Funcionario.filter(setor="Teste", salario=1000).first()
    assert primeiro is not None
    assert primeiro.nome == "Primeiro"

def test_count(session):
    session.execute(f"DROP TABLE IF EXISTS {Funcionario.__table_name__}")
    Funcionario.sync_table()
    
    for i in range(3):
        Funcionario.create(setor="Contagem", salario=1000+i, nome=f"Func{i}", id=uuid.uuid4())
    
    count = Funcionario.filter(setor="Contagem").count()
    assert count == 3