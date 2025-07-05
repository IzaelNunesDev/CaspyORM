# caspyorm/_internal/schema_sync.py
from typing import Dict, Any, List, Set, Tuple, Type
from caspyorm.connection import get_cluster, get_session, execute
from . import query_builder
import logging

logger = logging.getLogger(__name__)

def get_cassandra_table_schema(keyspace: str, table_name: str) -> Dict[str, Any] | None:
    """
    Busca os metadados de uma tabela existente no Cassandra e os retorna em um formato
    compatível com nosso __caspy_schema__.
    """
    cluster = get_cluster()
    if not cluster:
        return None

    try:
        table_meta = cluster.metadata.keyspaces[keyspace].tables[table_name]
    except KeyError:
        return None  # Tabela não existe

    cassandra_schema = {
        'table_name': table_meta.name,
        'fields': {col.name: {'type': str(col.cql_type)} for col in table_meta.columns.values()},
        'partition_keys': [col.name for col in table_meta.partition_key],
        'clustering_keys': [col.name for col in table_meta.clustering_key],
        'indexes': [idx.name for idx in table_meta.indexes.values()]
    }
    # Chave primária completa para facilitar a comparação
    cassandra_schema['primary_keys'] = cassandra_schema['partition_keys'] + cassandra_schema['clustering_keys']
    
    return cassandra_schema

def compare_schemas(model_schema: Dict[str, Any], db_schema: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Compara o schema do modelo com o schema do banco de dados e retorna as diferenças.
    """
    diffs: Dict[str, List[str]] = {
        'added_in_model': [],
        'removed_from_model': [],
        'type_mismatch': [],
        'pk_mismatch': [],
    }

    model_fields: Set[str] = set(model_schema['fields'].keys())
    db_fields: Set[str] = set(db_schema['fields'].keys())

    # 1. Campos adicionados no modelo (precisam ser adicionados no DB)
    added_fields = model_fields - db_fields
    diffs['added_in_model'] = list(added_fields)

    # 2. Campos removidos do modelo (precisam ser removidos do DB)
    removed_fields = db_fields - model_fields
    diffs['removed_from_model'] = list(removed_fields)

    # 3. Campos com tipo diferente
    common_fields = model_fields.intersection(db_fields)
    for field in common_fields:
        model_type = model_schema['fields'][field]['type']
        db_type = db_schema['fields'][field]['type']
        if model_type != db_type:
            diffs['type_mismatch'].append(f"Campo '{field}': modelo ({model_type}) != DB ({db_type})")

    # 4. Diferenças na chave primária
    if sorted(model_schema['primary_keys']) != sorted(db_schema['primary_keys']):
        diffs['pk_mismatch'].append(
            f"Chave Primária: modelo ({model_schema['primary_keys']}) != DB ({db_schema['primary_keys']})"
        )

    return diffs

def apply_schema_changes(model_schema: Dict[str, Any], diffs: Dict[str, List[str]]):
    """
    Gera e executa as queries CQL para aplicar as mudanças de schema detectadas.
    """
    table_name = model_schema['table_name']
    
    print("\n🚀 Aplicando alterações no schema...")

    # --- Adicionar Colunas ---
    if diffs['added_in_model']:
        for field_name in diffs['added_in_model']:
            field_details = model_schema['fields'][field_name]
            cql = query_builder.build_add_column_cql(
                table_name,
                column_name=field_name,
                column_type=field_details['type']
            )
            print(f"  [+] Executando: {cql}")
            try:
                execute(cql)
                logger.info(f"Coluna '{field_name}' adicionada com sucesso")
            except Exception as e:
                print(f"  [!] ERRO ao adicionar coluna '{field_name}': {e}")
                logger.error(f"Erro ao adicionar coluna '{field_name}': {e}")
    
    # --- Avisos para operações não suportadas ---
    if diffs['removed_from_model']:
        print("\n  [!] AVISO: A remoção automática de colunas não é suportada por segurança.")
        for field_name in diffs['removed_from_model']:
             print(f"      - Operação manual necessária: ALTER TABLE {table_name} DROP {field_name};")
    
    if diffs['type_mismatch']:
        print("\n  [!] AVISO: A alteração automática de tipo de coluna não é suportada.")
        for mismatch in diffs['type_mismatch']:
            print(f"      - Operação manual necessária para: {mismatch}")
            
    if diffs['pk_mismatch']:
        print("\n  [!] ERRO CRÍTICO: A alteração de chave primária não é possível no Cassandra.")
        print("      - A tabela deve ser recriada para aplicar esta mudança.")
        
    print("\n✅ Aplicação de schema concluída.")

def _create_indexes(table_name: str, schema: Dict[str, Any]) -> None:
    """Cria índices secundários se definidos no schema."""
    indexes = schema.get('indexes', [])
    
    for index_field in indexes:
        try:
            index_name = f"{table_name}_{index_field}_idx"
            create_index_query = f"""
                CREATE INDEX IF NOT EXISTS {index_name} 
                ON {table_name} ({index_field})
            """
            execute(create_index_query)
            logger.info(f"Índice '{index_name}' criado com sucesso")
            
        except Exception as e:
            logger.warning(f"Erro ao criar índice para '{index_field}': {e}")
            # Não falha a sincronização se o índice falhar

def sync_table(model_cls: Type, auto_apply: bool = False, verbose: bool = True) -> None:
    """
    Sincroniza o schema da tabela no Cassandra com a definição do modelo.
    """
    model_schema = model_cls.__caspy_schema__
    table_name = model_schema['table_name']
    session = get_session()
    keyspace = session.keyspace

    db_schema = get_cassandra_table_schema(keyspace, table_name)

    if db_schema is None:
        # Tabela não existe, então a criamos
        if verbose:
            print(f"Tabela '{table_name}' não encontrada. Criando...")
        
        create_table_query = query_builder.build_create_table_cql(model_schema)
        
        if verbose:
            print(f"Executando CQL para criar tabela:\n{create_table_query}")
        
        execute(create_table_query)
        
        if verbose:
            print("Tabela criada com sucesso.")
        
        # Criar índices se necessário
        _create_indexes(table_name, model_schema)
        return

    # Tabela existe, vamos comparar os schemas
    diffs = compare_schemas(model_schema, db_schema)
    
    # Remove as categorias de diferenças que estão vazias
    has_diffs = any(diffs.values())

    if not has_diffs:
        if verbose:
            print(f"✅ Schema da tabela '{table_name}' está sincronizado.")
        return

    # Etapa 3: Relatar as diferenças
    if verbose:
        print(f"⚠️  Schema da tabela '{table_name}' está dessincronizado!")
        
        if diffs['added_in_model']:
            print("\n  [+] Campos a serem ADICIONADOS na tabela:")
            for field in diffs['added_in_model']:
                print(f"      - {field} (tipo: {model_schema['fields'][field]['type']})")
        
        if diffs['removed_from_model']:
            print("\n  [-] Campos a serem REMOVIDOS da tabela:")
            for field in diffs['removed_from_model']:
                print(f"      - {field} (tipo: {db_schema['fields'][field]['type']})")

        if diffs['type_mismatch']:
            print("\n  [~] Campos com TIPOS DIFERENTES:")
            for mismatch in diffs['type_mismatch']:
                print(f"      - {mismatch}")

        if diffs['pk_mismatch']:
            print("\n  [!] Chave primária diferente:")
            for mismatch in diffs['pk_mismatch']:
                print(f"      - {mismatch}")
    
    # Etapa 4: Aplicar alterações se auto_apply=True
    if auto_apply:
        apply_schema_changes(model_schema, diffs)
    else:
        if verbose:
            print("\nExecute sync_table(auto_apply=True) para aplicar as mudanças automaticamente.")