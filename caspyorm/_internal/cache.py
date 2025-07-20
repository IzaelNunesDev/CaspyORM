# caspyorm/_internal/cache.py

from typing import Any, Dict, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

class SchemaCache:
    """Cache para schemas de tabelas para evitar queries repetidas."""
    
    def __init__(self, max_size: int = 128):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
    
    def get(self, keyspace: str, table_name: str) -> Optional[Dict[str, Any]]:
        """Obtém um schema do cache."""
        key = f"{keyspace}.{table_name}"
        return self._cache.get(key)
    
    def set(self, keyspace: str, table_name: str, schema: Dict[str, Any]) -> None:
        """Armazena um schema no cache."""
        key = f"{keyspace}.{table_name}"
        
        # Implementar LRU simples se o cache estiver cheio
        if len(self._cache) >= self._max_size:
            # Remove o primeiro item (mais antigo)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"Removido schema do cache: {oldest_key}")
        
        self._cache[key] = schema
        logger.debug(f"Schema armazenado no cache: {key}")
    
    def clear(self) -> None:
        """Limpa o cache."""
        self._cache.clear()
        logger.debug("Cache de schemas limpo")
    
    def invalidate(self, keyspace: str, table_name: str) -> None:
        """Invalida um schema específico no cache."""
        key = f"{keyspace}.{table_name}"
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Schema invalidado no cache: {key}")

# Instância global do cache
schema_cache = SchemaCache()

@lru_cache(maxsize=256)
def get_cached_table_schema(keyspace: str, table_name: str) -> Optional[Dict[str, Any]]:
    """
    Decorator para cachear schemas de tabelas usando functools.lru_cache.
    Esta função é usada como fallback para o cache manual.
    """
    return None  # Será implementado quando necessário

class PreparedStatementCache:
    """Cache para prepared statements para melhorar performance."""
    
    def __init__(self, max_size: int = 256):
        self._cache: Dict[str, Any] = {}
        self._max_size = max_size
    
    def get(self, query: str) -> Optional[Any]:
        """Obtém uma prepared statement do cache."""
        return self._cache.get(query)
    
    def set(self, query: str, prepared_statement: Any) -> None:
        """Armazena uma prepared statement no cache."""
        # Implementar LRU simples se o cache estiver cheio
        if len(self._cache) >= self._max_size:
            # Remove o primeiro item (mais antigo)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"Removida prepared statement do cache: {oldest_key[:50]}...")
        
        self._cache[query] = prepared_statement
        logger.debug(f"Prepared statement armazenada no cache: {query[:50]}...")
    
    def clear(self) -> None:
        """Limpa o cache."""
        self._cache.clear()
        logger.debug("Cache de prepared statements limpo")

# Instância global do cache de prepared statements
prepared_statement_cache = PreparedStatementCache()

def measure_performance(func):
    """Decorator para medir performance de operações."""
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"{func.__name__} executada em {duration:.4f} segundos")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} falhou após {duration:.4f} segundos: {e}")
            raise
    
    return wrapper

def measure_performance_async(func):
    """Decorator para medir performance de operações assíncronas."""
    import time
    from functools import wraps
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"{func.__name__} executada em {duration:.4f} segundos")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} falhou após {duration:.4f} segundos: {e}")
            raise
    
    return wrapper 