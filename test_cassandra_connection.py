from cassandra.cluster import Cluster

try:
    # Tenta conectar ao Cassandra local
    cluster = Cluster(['127.0.0.1'])
    session = cluster.connect()
    print("✅ Conectado ao Cassandra com sucesso!")
    
    # Mostra informações da versão do Cassandra
    rows = session.execute("SELECT release_version FROM system.local")
    for row in rows:
        print(f"📊 Versão do Cassandra: {row.release_version}")
    
    # Fecha a conexão
    session.shutdown()
    cluster.shutdown()
    
except Exception as e:
    print(f"❌ Erro ao conectar ao Cassandra: {e}")
