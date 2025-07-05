"""
Configuração do banco de dados para a aplicação de demonstração.
"""
from caspyorm import connection

def setup_database():
    """Configura a conexão com o Cassandra."""
    try:
        connection.connect(
            contact_points=['localhost'],
            keyspace='caspyorm_demo',
            protocol_version=5
        )
        print("✅ Conectado ao Cassandra com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao conectar ao Cassandra: {e}")
        return False

def create_keyspace():
    """Cria o keyspace se não existir."""
    try:
        from cassandra.cluster import Cluster
        cluster = Cluster(['localhost'])
        session = cluster.connect()
        
        # Criar keyspace se não existir
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS caspyorm_demo 
            WITH replication = {
                'class': 'SimpleStrategy',
                'replication_factor': 1
            }
        """)
        
        session.shutdown()
        cluster.shutdown()
        print("✅ Keyspace 'caspyorm_demo' criado/verificado!")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar keyspace: {e}")
        return False 