from cassandra.cluster import Cluster

KEYSPACE = "caspyorm_test_suite"
TABLES = ["users_real_test", "products_real_test"]

def main():
    cluster = Cluster(["127.0.0.1"], port=9042)
    session = cluster.connect(KEYSPACE)
    print(f"Tabelas no keyspace {KEYSPACE}:")
    rows = session.execute("SELECT table_name FROM system_schema.tables WHERE keyspace_name=%s", (KEYSPACE,))
    for row in rows:
        print(" -", row.table_name)
    for table in TABLES:
        print(f"\nSchema da tabela {table}:")
        rows = session.execute("SELECT column_name, kind, type FROM system_schema.columns WHERE keyspace_name=%s AND table_name=%s", (KEYSPACE, table))
        for row in rows:
            print(f"  {row.column_name} ({row.kind}): {row.type}")
    cluster.shutdown()

if __name__ == "__main__":
    main() 