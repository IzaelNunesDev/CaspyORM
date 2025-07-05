# caspyorm/connection.py

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from typing import List, Optional, Dict, Any
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    """Gerencia a conexão com o cluster Cassandra."""
    
    def __init__(self):
        self.cluster: Optional[Cluster] = None
        self.session = None
        self.keyspace: Optional[str] = None
        self._is_connected = False
    
    def connect(
        self, 
        contact_points: List[str] = ['127.0.0.1'],
        port: int = 9042,
        keyspace: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Conecta ao cluster Cassandra.
        
        Args:
            contact_points: Lista de endereços dos nós do cluster
            port: Porta do Cassandra (padrão: 9042)
            keyspace: Keyspace para usar
            username: Usuário para autenticação (opcional)
            password: Senha para autenticação (opcional)
        """
        try:
            # Configurar autenticação se fornecida
            auth_provider = None
            if username and password:
                auth_provider = PlainTextAuthProvider(username=username, password=password)
            
            # Criar cluster
            self.cluster = Cluster(
                contact_points=contact_points,
                port=port,
                auth_provider=auth_provider,
                **kwargs
            )
            
            # Conectar e obter sessão
            self.session = self.cluster.connect()
            self._is_connected = True
            
            # Usar keyspace se especificado
            if keyspace:
                self.use_keyspace(keyspace)
            
            logger.info(f"Conectado ao Cassandra em {contact_points}:{port}")
            
        except Exception as e:
            logger.error(f"Erro ao conectar ao Cassandra: {e}")
            raise
    
    def use_keyspace(self, keyspace: str) -> None:
        """Define o keyspace ativo."""
        if not self.session:
            raise RuntimeError("Não há conexão ativa com o Cassandra")
        
        try:
            # Criar keyspace se não existir
            self.session.execute(f"""
                CREATE KEYSPACE IF NOT EXISTS {keyspace}
                WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
            """)
            
            # Usar o keyspace
            self.session.set_keyspace(keyspace)
            self.keyspace = keyspace
            
            logger.info(f"Usando keyspace: {keyspace}")
            
        except Exception as e:
            logger.error(f"Erro ao usar keyspace {keyspace}: {e}")
            raise
    
    def execute(self, query: str, parameters: Optional[Any] = None):
        """Executa uma query CQL."""
        if not self.session:
            raise RuntimeError("Não há conexão ativa com o Cassandra")
        try:
            if parameters is not None:
                return self.session.execute(query, parameters)
            else:
                return self.session.execute(query)
        except Exception as e:
            logger.error(f"Erro ao executar query: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parâmetros: {parameters}")
            raise
    
    def disconnect(self) -> None:
        """Desconecta do cluster Cassandra."""
        if self.session:
            self.session.shutdown()
            self.session = None
        
        if self.cluster:
            self.cluster.shutdown()
            self.cluster = None
        
        self._is_connected = False
        self.keyspace = None
        
        logger.info("Desconectado do Cassandra")
    
    @property
    def is_connected(self) -> bool:
        """Verifica se há uma conexão ativa."""
        return self._is_connected and self.session is not None
    
    def get_cluster(self) -> Optional[Cluster]:
        """Retorna a instância do cluster ativo."""
        return self.cluster
    
    def get_session(self):
        """
        Retorna a sessão ativa do Cassandra.
        Garante que a conexão foi estabelecida.
        """
        if not self.session:
            raise RuntimeError("A conexão com o Cassandra não foi estabelecida. Chame `connection.connect()` primeiro.")
        return self.session

# Instância global do gerenciador de conexão
connection = ConnectionManager()

# Funções de conveniência
def connect(**kwargs):
    """Conecta ao Cassandra usando a instância global."""
    connection.connect(**kwargs)

def disconnect():
    """Desconecta do Cassandra usando a instância global."""
    connection.disconnect()

def execute(query: str, parameters: Optional[Any] = None):
    """Executa uma query usando a instância global."""
    return connection.execute(query, parameters)

def get_cluster() -> Optional[Cluster]:
    """Retorna a instância do cluster ativo."""
    return connection.get_cluster()

def get_session():
    """
    Retorna a sessão ativa do Cassandra.
    Garante que a conexão foi estabelecida.
    """
    return connection.get_session()