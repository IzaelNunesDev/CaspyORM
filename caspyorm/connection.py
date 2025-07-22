# caspyorm/connection.py

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from typing import List, Optional, Dict, Any
import logging
import asyncio

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    """Gerencia a conexão com o cluster Cassandra."""
    
    def __init__(self):
        self.cluster: Optional[Cluster] = None
        self.session = None
        self.async_session = None  # Sessão para operações assíncronas
        self.keyspace: Optional[str] = None
        self._is_connected = False
        self._is_async_connected = False  # Flag para conexão assíncrona
    
    def connect(
        self,
        keyspace: str,
        contact_points: Optional[List[str]] = None,
        port: int = 9042,
        secure_connect_bundle: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        ssl_options: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """
        Conecta ao cluster Cassandra (síncrono).
        """
        try:
            if self.cluster:
                return

            if secure_connect_bundle:
                if contact_points:
                    logger.warning("Both 'secure_connect_bundle' and 'contact_points' provided. Ignoring 'contact_points'.")
                cluster_kwargs = {"cloud": {"secure_connect_bundle": secure_connect_bundle}}
            elif contact_points:
                cluster_kwargs = {"contact_points": contact_points, "port": port}
            else:
                raise ValueError("You must provide either 'contact_points' or 'secure_connect_bundle'.")

            if username and password:
                auth_provider = PlainTextAuthProvider(username=username, password=password)
                cluster_kwargs['auth_provider'] = auth_provider

            if ssl_options:
                cluster_kwargs['ssl_options'] = ssl_options
            
            self.cluster = Cluster(**cluster_kwargs, **kwargs)
            self.session = self.cluster.connect(keyspace)
            self._is_connected = True
            self.keyspace = keyspace
            
            log_target = secure_connect_bundle if secure_connect_bundle else f"{contact_points}:{port}"
            logger.info(f"Conectado ao Cassandra (SÍNCRONO) em {log_target}")
            
        except Exception as e:
            logger.error(f"Erro ao conectar ao Cassandra: {e}")
            raise

    async def connect_async(
        self,
        keyspace: str,
        contact_points: Optional[List[str]] = None,
        port: int = 9042,
        secure_connect_bundle: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        ssl_options: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """
        Conecta ao cluster Cassandra (assíncrono).
        """
        try:
            if self.async_session:
                 return

            if secure_connect_bundle:
                if contact_points:
                    logger.warning("Both 'secure_connect_bundle' and 'contact_points' provided. Ignoring 'contact_points'.")
                cluster_kwargs = {"cloud": {"secure_connect_bundle": secure_connect_bundle}}
            elif contact_points:
                cluster_kwargs = {"contact_points": contact_points, "port": port}
            else:
                raise ValueError("You must provide either 'contact_points' or 'secure_connect_bundle'.")

            if username and password:
                auth_provider = PlainTextAuthProvider(username=username, password=password)
                cluster_kwargs['auth_provider'] = auth_provider

            if ssl_options:
                cluster_kwargs['ssl_options'] = ssl_options
            
            self.cluster = Cluster(**cluster_kwargs, **kwargs)
            self.async_session = self.cluster.connect()
            self._is_async_connected = True
            
            if keyspace:
                self.use_keyspace_async(keyspace)
            
            logger.info(f"Conectado ao Cassandra (ASSÍNCRONO) em {contact_points}:{port}")
            
        except Exception as e:
            logger.error(f"Erro ao conectar ao Cassandra (async): {e}")
            raise
    
    def use_keyspace(self, keyspace: str) -> None:
        """Define o keyspace ativo (síncrono)."""
        if not self.session:
            raise RuntimeError("Não há conexão ativa com o Cassandra")
        
        try:
            self.session.execute(f"""
                CREATE KEYSPACE IF NOT EXISTS {keyspace}
                WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
            """)
            self.session.set_keyspace(keyspace)
            self.keyspace = keyspace
            logger.info(f"Usando keyspace (SÍNCRONO): {keyspace}")
        except Exception as e:
            logger.error(f"Erro ao usar keyspace {keyspace}: {e}")
            raise

    def use_keyspace_async(self, keyspace: str) -> None:
        """Define o keyspace ativo (assíncrono)."""
        if not self.async_session:
            raise RuntimeError("Não há conexão assíncrona ativa com o Cassandra")
        
        try:
            self.async_session.execute(f"""
                CREATE KEYSPACE IF NOT EXISTS {keyspace}
                WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
            """)
            self.async_session.set_keyspace(keyspace)
            self.keyspace = keyspace
            logger.info(f"Usando keyspace (ASSÍNCRONO): {keyspace}")
        except Exception as e:
            logger.error(f"Erro ao usar keyspace {keyspace} (async): {e}")
            raise

    def execute(self, query: str, parameters: Optional[Any] = None):
        """Executa uma query CQL (síncrono)."""
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

    async def execute_async(self, query: str, parameters: Optional[Any] = None):
        """Executa uma query CQL (assíncrono)."""
        if not self.async_session:
            raise RuntimeError("Não há conexão assíncrona ativa com o Cassandra")
        try:
            if parameters is not None:
                future = self.async_session.execute_async(query, parameters)
            else:
                future = self.async_session.execute_async(query)
            return await asyncio.wrap_future(future)
        except Exception as e:
            logger.error(f"Erro ao executar query (async): {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parâmetros: {parameters}")
            raise
    
    def disconnect(self) -> None:
        """Desconecta do cluster Cassandra (síncrono)."""
        if self.session:
            self.session.shutdown()
            self.session = None
        if self.cluster:
            self.cluster.shutdown()
            self.cluster = None
        self._is_connected = False
        self.keyspace = None
        logger.info("Desconectado do Cassandra (SÍNCRONO)")

    async def disconnect_async(self) -> None:
        """Desconecta do cluster Cassandra (assíncrono)."""
        if self.async_session:
            self.async_session.shutdown()
            self.async_session = None
        if self.cluster:
            self.cluster.shutdown()
            self.cluster = None
        self._is_async_connected = False
        self.keyspace = None
        logger.info("Desconectado do Cassandra (ASSÍNCRONO)")
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected and self.session is not None

    @property
    def is_async_connected(self) -> bool:
        return self._is_async_connected and self.async_session is not None
    
    def get_cluster(self) -> Optional[Cluster]:
        return self.cluster
    
    def get_session(self):
        if not self.session or not self._is_connected:
            raise RuntimeError("A conexão com o Cassandra não foi estabelecida. Chame `connection.connect()` primeiro.")
        return self.session

    def get_async_session(self):
        if not self.async_session or not self._is_async_connected:
            raise RuntimeError("A conexão assíncrona com o Cassandra não foi estabelecida. Chame `connection.connect_async()` primeiro.")
        return self.async_session

connection = ConnectionManager()

def connect(**kwargs):
    connection.connect(**kwargs)

def disconnect():
    connection.disconnect()

def execute(query: str, parameters: Optional[Any] = None):
    return connection.execute(query, parameters)

def get_cluster() -> Optional[Cluster]:
    return connection.get_cluster()

def get_session():
    return connection.get_session()

async def connect_async(**kwargs):
    await connection.connect_async(**kwargs)

async def disconnect_async():
    """Desconecta do Cassandra usando a instância global (assíncrono)."""
    await connection.disconnect_async()

async def execute_async(query: str, parameters: Optional[Any] = None):
    """Executa uma query usando a instância global (assíncrono)."""
    return await connection.execute_async(query, parameters)

def get_async_session():
    """
    Retorna a sessão assíncrona ativa do Cassandra.
    Garante que a conexão assíncrona foi estabelecida.
    """
    return connection.get_async_session()