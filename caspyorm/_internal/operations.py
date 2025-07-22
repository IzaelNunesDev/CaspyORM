# caspyorm/_internal/operations.py

import asyncio
from typing import Any, Dict, List, Optional, Type
import logging
from cassandra import DriverException
from cassandra.cluster import NoHostAvailable
from cassandra.connection import ConnectionException
from cassandra.query import BatchStatement, SimpleStatement
from cassandra import ConsistencyLevel

from ..exceptions import CaspyORMException, ValidationError
from ..connection import get_session, get_async_session
from . import query_builder
from .cache import prepared_statement_cache

logger = logging.getLogger(__name__)

def _handle_cassandra_exception(e: Exception, operation: str) -> None:
    """Trata exceções específicas do Cassandra e as converte em exceções do CaspyORM."""
    if isinstance(e, (DriverException, NoHostAvailable, ConnectionException)):
        raise CaspyORMException(f"Database operation failed during {operation}: {str(e)}") from e
    else:
        # Re-raise outras exceções como estão
        raise

def save_instance(instance) -> None:
    """Salva (insere ou atualiza) uma instância no Cassandra (síncrono)."""
    try:
        # Validar chaves primárias antes de salvar
        _validate_primary_keys(instance)
        
        # Construir query INSERT
        cql = query_builder.build_insert_cql(instance.__caspy_schema__)
        
        # Preparar e executar com cache
        session = get_session()
        prepared = prepared_statement_cache.get(cql)
        if prepared is None:
            prepared = session.prepare(cql)
            prepared_statement_cache.set(cql, prepared)
        session.execute(prepared, list(instance.model_dump().values()))
        
        logger.info(f"Instância salva: {instance.__class__.__name__}")
        
    except Exception as e:
        _handle_cassandra_exception(e, "save operation")

async def save_instance_async(instance, timeout: int = 30) -> None:
    """Salva (insere ou atualiza) uma instância no Cassandra (assíncrono)."""
    try:
        # Validar chaves primárias antes de salvar
        _validate_primary_keys(instance)
        
        # Construir query INSERT
        cql = query_builder.build_insert_cql(instance.__caspy_schema__)
        
        # Preparar e executar com cache
        session = get_async_session()
        prepared = prepared_statement_cache.get(cql)
        if prepared is None:
            prepared = session.prepare(cql)
            prepared_statement_cache.set(cql, prepared)
        future = session.execute_async(prepared, list(instance.model_dump().values()))
        
        # Aguardar resultado com timeout
        await asyncio.wait_for(_wait_for_cassandra_future(future), timeout=timeout)
        
        logger.info(f"Instância salva (ASSÍNCRONO): {instance.__class__.__name__}")
        
    except asyncio.TimeoutError:
        raise CaspyORMException(f"Database operation timed out after {timeout} seconds during async save operation")
    except Exception as e:
        _handle_cassandra_exception(e, "async save operation")

def get_one(model_cls: Type, **kwargs: Any) -> Optional[Any]:
    """Busca um único registro (síncrono)."""
    try:
        from ..query import QuerySet
        queryset = QuerySet(model_cls).filter(**kwargs).limit(1)
        results = list(queryset)
        return results[0] if results else None
    except Exception as e:
        _handle_cassandra_exception(e, "get_one operation")
        return None

async def get_one_async(model_cls: Type, **kwargs: Any) -> Optional[Any]:
    """Busca um único registro (assíncrono)."""
    try:
        from ..query import QuerySet
        queryset = QuerySet(model_cls).filter(**kwargs).limit(1)
        results = await queryset.all_async()
        return results[0] if results else None
    except Exception as e:
        _handle_cassandra_exception(e, "async get_one operation")
        return None

def filter_query(model_cls: Type, **kwargs: Any):
    """Inicia uma query com filtros e retorna um QuerySet (síncrono)."""
    from ..query import QuerySet
    return QuerySet(model_cls).filter(**kwargs)

def _validate_primary_keys(instance) -> None:
    """Valida se as chaves primárias não são nulas antes de salvar."""
    # Verificar se o modelo tem chaves primárias definidas
    primary_keys = instance.__caspy_schema__.get('primary_keys')
    if not primary_keys:
        raise ValidationError("Modelo deve ter pelo menos uma chave primária")
    for pk_name in primary_keys:
        field = instance.model_fields[pk_name]
        value = getattr(instance, pk_name, None)
        # Verificar se é um campo UUID com valor padrão automático
        from ..fields import UUID
        is_uuid_with_auto_default = (
            isinstance(field, UUID) and 
            field.primary_key and 
            field.default is not None
        )
        # Se o valor é None e o campo não tem valor padrão (exceto UUIDs automáticos), é um erro
        if value is None and field.default is None and not is_uuid_with_auto_default:
            raise ValidationError(f"Primary key '{pk_name}' cannot be None before saving.")
        # Se o campo tem valor padrão mas ainda é None, aplicar o valor padrão
        if value is None and field.default is not None:
            default_value = field.default() if callable(field.default) else field.default
            setattr(instance, pk_name, default_value)

async def _wait_for_cassandra_future(future):
    """Aguarda um ResponseFuture do Cassandra driver de forma não-bloqueante, evitando deadlocks.
    Usa asyncio.to_thread (Python 3.9+) para evitar problemas de event loop.
    """
    import asyncio
    try:
        if hasattr(asyncio, 'to_thread'):
            # Python 3.9+: mais seguro, evita deadlocks
            return await asyncio.to_thread(future.result)
        else:
            # Compatibilidade com versões anteriores
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, future.result)
    except Exception as e:
        _handle_cassandra_exception(e, "future operation") 