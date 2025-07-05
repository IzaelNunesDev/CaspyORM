#!/usr/bin/env python3
"""
Script para limpar as tabelas do Cassandra.
"""
from cassandra.cluster import Cluster

def clean_tables():
    """Remove as tabelas users e posts do keyspace caspyorm_demo."""
    try:
        # Conectar ao Cassandra
        cluster = Cluster(['localhost'])
        session = cluster.connect('caspyorm_demo')
        
        # Dropar tabelas
        session.execute('DROP TABLE IF EXISTS users')
        session.execute('DROP TABLE IF EXISTS posts')
        
        print("✅ Tabelas 'users' e 'posts' removidas com sucesso!")
        
        # Fechar conexão
        session.shutdown()
        cluster.shutdown()
        
        return True
    except Exception as e:
        print(f"❌ Erro ao remover tabelas: {e}")
        return False

if __name__ == "__main__":
    clean_tables() 