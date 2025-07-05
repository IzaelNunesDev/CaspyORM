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
        
        # Garante que a conexão está ativa
        session = connection.get_session()
        
        # 'yield' passa o controle para os testes
        yield session
        
    finally:
        # Limpeza após a execução de todos os testes
        logger.info(f"Limpando o keyspace de teste '{TEST_KEYSPACE}'...")
        try:
            # Opcional: Apagar o keyspace de teste para um ambiente 100% limpo na próxima execução
            # connection.execute(f"DROP KEYSPACE IF EXISTS {TEST_KEYSPACE}")
            connection.disconnect()
            logger.info("Desconectado do Cassandra.")
        except:
            pass  # Ignora erros de desconexão

@pytest.fixture(scope="function")
def session(cassandra_session):
    """
    Fixture de escopo de FUNÇÃO. Fornece a sessão para cada teste,
    garantindo que é uma referência válida mesmo após reconexões.
    """
    # A fixture cassandra_session garante que a conexão existe.
    # Esta fixture apenas passa a referência. Como agora é function-scoped,
    # ela reavalia `connection.get_session()` para cada teste.
    return connection.get_session()

@pytest.fixture(scope="session", autouse=True)
async def cassandra_async_session(cassandra_session):
    """
    Fixture do Pytest que estabelece a conexão assíncrona com o Cassandra.
    Executa após a conexão síncrona estar estabelecida.
    """
    try:
        # Conecta de forma assíncrona usando o mesmo keyspace
        await connection.connect_async(contact_points=['127.0.0.1'], keyspace=TEST_KEYSPACE)
        logger.info(f"Conectado ao Cassandra (ASSÍNCRONO) no keyspace de teste '{TEST_KEYSPACE}'")
        
        # Garante que a conexão assíncrona está ativa
        async_session = connection.get_async_session()
        
        # 'yield' passa o controle para os testes
        yield async_session
        
    finally:
        # Limpeza da conexão assíncrona
        try:
            await connection.disconnect_async()
            logger.info("Desconectado do Cassandra (ASSÍNCRONO).")
        except Exception:
            pass  # Ignora erros de desconexão

@pytest.fixture(scope="function")
def async_session(cassandra_async_session):
    """
    Fixture de escopo de FUNÇÃO. Fornece a sessão assíncrona para cada teste.
    """
    return connection.get_async_session() 