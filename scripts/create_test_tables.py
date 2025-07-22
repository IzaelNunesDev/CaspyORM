from cassandra.cluster import Cluster

KEYSPACE = "caspyorm_test_suite"

CREATE_USERS_TABLE = f"""
CREATE TABLE IF NOT EXISTS {KEYSPACE}.users_real_test (
    id uuid PRIMARY KEY,
    name text,
    email text,
    age int,
    created_at timestamp,
    tags list<text>,
    roles set<text>,
    metadata map<text, text>
);
"""

CREATE_PRODUCTS_TABLE = f"""
CREATE TABLE IF NOT EXISTS {KEYSPACE}.products_real_test (
    id uuid PRIMARY KEY,
    name text,
    price int,
    category text,
    in_stock int
);
"""

CREATE_EMAIL_INDEX = f"""
CREATE INDEX IF NOT EXISTS ON {KEYSPACE}.users_real_test (email);
"""

CREATE_CATEGORY_INDEX = f"""
CREATE INDEX IF NOT EXISTS ON {KEYSPACE}.products_real_test (category);
"""

def main():
    cluster = Cluster(["127.0.0.1"], port=9042)
    session = cluster.connect(KEYSPACE)
    print("Criando tabela users_real_test...")
    session.execute(CREATE_USERS_TABLE)
    print("Criando tabela products_real_test...")
    session.execute(CREATE_PRODUCTS_TABLE)
    print("Criando índice de email em users_real_test...")
    session.execute(CREATE_EMAIL_INDEX)
    print("Criando índice de category em products_real_test...")
    session.execute(CREATE_CATEGORY_INDEX)
    print("Tabelas criadas com sucesso.")
    cluster.shutdown()

if __name__ == "__main__":
    main() 