# caspyorm/_internal/connection_pool.py

from typing import List, Optional, Dict, Any
from cassandra.cluster import Cluster, Session
from cassandra.auth import PlainTextAuthProvider
from cassandra.policies import DCAwareRoundRobinPolicy, TokenAwarePolicy
from cassandra.pool import Host
import logging
import threading
import time

logger = logging.getLogger(__name__)

class ConnectionPool:
    """Pool de conexões para o Cassandra com configurações otimizadas."""
    
    def __init__(self, max_connections: int = 10, max_retries: int = 3):
        self.max_connections = max_connections
        self.max_retries = max_retries
        self._cluster: Optional[Cluster] = None
        self._session: Optional[Session] = None
        self._keyspace: Optional[str] = None
        self._lock = threading.Lock()
        self._connection_config: Optional[Dict[str, Any]] = None
        
    def configure(
        self,
        contact_points: List[str] = ['127.0.0.1'],
        port: int = 9042,
        keyspace: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        connection_timeout: int = 10,
        request_timeout: int = 10,
        **kwargs: Any
    ) -> None:
        """
        Configura o pool de conexões.
        
        Args:
            contact_points: Lista de pontos de contato do Cassandra
            port: Porta do Cassandra
            keyspace: Keyspace a ser usado
            username: Nome de usuário para autenticação
            password: Senha para autenticação
            connection_timeout: Timeout para estabelecer conexão (segundos)
            request_timeout: Timeout para requisições (segundos)
            **kwargs: Configurações adicionais do cluster
        """
        self._connection_config = {
            'contact_points': contact_points,
            'port': port,
            'keyspace': keyspace,
            'username': username,
            'password': password,
            'connection_timeout': connection_timeout,
            'request_timeout': request_timeout,
            **kwargs
        }
        
    def connect(self) -> Session:
        """Estabelece conexão com o cluster Cassandra usando configurações otimizadas."""
        if self._session is not None:
            return self._session
            
        with self._lock:
            if self._session is not None:
                return self._session
                
            if not self._connection_config:
                raise RuntimeError("Connection pool não foi configurado. Chame configure() primeiro.")
            
            try:
                # Configurar autenticação se fornecida
                auth_provider = None
                if self._connection_config.get('username') and self._connection_config.get('password'):
                    auth_provider = PlainTextAuthProvider(
                        username=self._connection_config['username'],
                        password=self._connection_config['password']
                    )
                
                # Configurar políticas de load balancing
                load_balancing_policy = TokenAwarePolicy(DCAwareRoundRobinPolicy())
                
                # Criar cluster com configurações otimizadas
                cluster_kwargs = {
                    'contact_points': self._connection_config['contact_points'],
                    'port': self._connection_config['port'],
                    'auth_provider': auth_provider,
                    'load_balancing_policy': load_balancing_policy,
                    # Configurações de pool de conexões
                    'max_schema_agreement_wait': 30,
                    # Configurações de timeout
                    'connect_timeout': self._connection_config.get('connection_timeout', 10),
                    'request_timeout': self._connection_config.get('request_timeout', 10),
                }
                
                # Adicionar configurações extras
                for k, v in self._connection_config.items():
                    if k not in ['contact_points', 'port', 'username', 'password', 'keyspace']:
                        cluster_kwargs[k] = v
                
                self._cluster = Cluster(**cluster_kwargs)
                
                # Conectar e obter sessão
                self._session = self._cluster.connect()
                
                # Usar keyspace se especificado
                if self._connection_config.get('keyspace'):
                    self.use_keyspace(self._connection_config['keyspace'])
                
                logger.info(f"Pool de conexões estabelecido com {self._connection_config['contact_points']}:{self._connection_config['port']}")
                return self._session
                
            except Exception as e:
                logger.error(f"Erro ao estabelecer pool de conexões: {e}")
                raise
    
    def use_keyspace(self, keyspace: str) -> None:
        """Define o keyspace ativo."""
        if not self._session:
            raise RuntimeError("Não há conexão ativa com o Cassandra")
        
        try:
            # Criar keyspace se não existir
            self._session.execute(f"""
                CREATE KEYSPACE IF NOT EXISTS {keyspace}
                WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
            """)
            
            # Usar o keyspace
            self._session.set_keyspace(keyspace)
            self._keyspace = keyspace
            
            logger.info(f"Usando keyspace: {keyspace}")
            
        except Exception as e:
            logger.error(f"Erro ao usar keyspace {keyspace}: {e}")
            raise
    
    def get_session(self) -> Session:
        """Retorna a sessão ativa, estabelecendo conexão se necessário."""
        if not self._session:
            return self.connect()
        return self._session
    
    def disconnect(self) -> None:
        """Desconecta do cluster Cassandra."""
        with self._lock:
            if self._session:
                self._session.shutdown()
                self._session = None
            
            if self._cluster:
                self._cluster.shutdown()
                self._cluster = None
            
            self._keyspace = None
            logger.info("Pool de conexões desconectado")
    
    @property
    def is_connected(self) -> bool:
        """Verifica se há uma conexão ativa."""
        return self._session is not None and not self._session.is_shutdown
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o cluster."""
        if not self._cluster or not self._cluster.metadata:
            return {}
        
        try:
            hosts = self._cluster.metadata.all_hosts()
            return {
                'hosts': [host.address for host in hosts],
                'keyspace': self._keyspace,
                'session_active': self._session is not None and not self._session.is_shutdown
            }
        except Exception as e:
            logger.warning(f"Erro ao obter informações do cluster: {e}")
            return {}
    
    def health_check(self) -> bool:
        """Verifica a saúde da conexão."""
        if not self._session:
            return False
        
        try:
            # Executar uma query simples para verificar a conexão
            self._session.execute("SELECT release_version FROM system.local")
            return True
        except Exception as e:
            logger.warning(f"Health check falhou: {e}")
            return False

# Instância global do pool de conexões
connection_pool = ConnectionPool()

def get_pooled_session() -> Session:
    """Retorna uma sessão do pool de conexões."""
    return connection_pool.get_session()

def configure_connection_pool(**kwargs) -> None:
    """Configura o pool de conexões global."""
    connection_pool.configure(**kwargs)

def disconnect_pool() -> None:
    """Desconecta o pool de conexões global."""
    connection_pool.disconnect()

def get_pool_health() -> bool:
    """Verifica a saúde do pool de conexões."""
    return connection_pool.health_check() 