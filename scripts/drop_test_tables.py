import sys
from cassandra.cluster import Cluster

KEYSPACE = "caspyorm_test_suite"
TABLES = ["users_real_test", "products_real_test"]

try:
    cluster = Cluster(["127.0.0.1"], port=9042)
    session = cluster.connect(KEYSPACE)
    for table in TABLES:
        print(f"Dropping table {KEYSPACE}.{table} ...")
        session.execute(f"DROP TABLE IF EXISTS {KEYSPACE}.{table};")
    print("Tabelas excluídas com sucesso.")
except Exception as e:
    print(f"Erro ao excluir tabelas: {e}")
    sys.exit(1)
finally:
    if 'cluster' in locals():
        cluster.shutdown() 