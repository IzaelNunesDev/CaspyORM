import pytest
import logging
from caspyorm import connection

# Configurar logging para os testes
logger = logging.getLogger("caspyorm.tests")

# Usamos um nome de keyspace específico para os testes para não interferir com dados de produção/dev
TEST_KEYSPACE = "caspyorm_test_suite"

@pytest.fixture(scope="session", autouse=True)
def cassandra_session():
    """
    Fixture do Pytest que estabelece a conexão com o Cassandra antes de todos os testes
    e a encerra depois que todos os testes forem executados.
    
    `scope="session"`: Executa apenas uma vez por sessão de teste.
    `autouse=True`: Aplica automaticamente a todos os testes.
    """
    try:
        # Conecta a um keyspace de teste, que será criado se não existir
        connection.connect(contact_points=['127.0.0.1'], keyspace=TEST_KEYSPACE)
        logger.info(f"Conectado ao Cassandra no keyspace de teste '{TEST_KEYSPACE}'")
        
        # 'yield' passa o controle para os testes
        yield connection.get_session()
        
    finally:
        # Limpeza após a execução de todos os testes
        logger.info(f"Limpando o keyspace de teste '{TEST_KEYSPACE}'...")
        try:
            if hasattr(connection, 'is_connected') and connection.is_connected:
                # Opcional: Apagar o keyspace de teste para um ambiente 100% limpo na próxima execução
                # connection.execute(f"DROP KEYSPACE IF EXISTS {TEST_KEYSPACE}")
                connection.disconnect()
                logger.info("Desconectado do Cassandra.")
        except:
            pass  # Ignora erros de desconexão

@pytest.fixture
def session(cassandra_session):
    """Fixture que fornece a sessão do Cassandra para cada teste."""
    return cassandra_session 