#!/usr/bin/env python3
"""
Teste de performance com ~1GB de dados reais do NYC TLC (yellow) - VERSÃO ULTRA-OTIMIZADA
Usa dados já baixados, chunks maiores e batches maiores para máxima velocidade.
"""

import os
import time
import pandas as pd
from datetime import datetime
from caspyorm import fields, Model, connection
import uuid
import logging
import psutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealTaxiTrip(Model):
    __table_name__ = 'real_nyc_taxi_trips_1gb_ultra'
    trip_id = fields.UUID(primary_key=True)
    vendor_id = fields.Text(partition_key=True)
    pickup_datetime = fields.Timestamp(clustering_key=True)
    passenger_count = fields.Integer()
    trip_distance = fields.Float()
    pickup_longitude = fields.Float()
    pickup_latitude = fields.Float()
    dropoff_longitude = fields.Float()
    dropoff_latitude = fields.Float()
    rate_code_id = fields.Integer()
    store_and_fwd_flag = fields.Text()
    payment_type = fields.Integer()
    fare_amount = fields.Float()
    extra = fields.Float()
    mta_tax = fields.Float()
    tip_amount = fields.Float()
    tolls_amount = fields.Float()
    improvement_surcharge = fields.Float()
    total_amount = fields.Float()
    created_at = fields.Timestamp(default=datetime.now)

# Usar dados já baixados se existirem
DATA_DIRS = ['nyc_real_data_1gb', 'nyc_real_data_1gb_fast', 'nyc_real_data']
KEYSPACE = 'nyc_taxi_real_1gb_ultra'
BATCH_SIZE = 50  # Batch maior
CHUNK_SIZE = 50000  # Chunk muito maior
TARGET_SIZE_GB = 1.0

def find_existing_data():
    """Procura por dados já baixados"""
    for data_dir in DATA_DIRS:
        if os.path.exists(data_dir):
            files = [f for f in os.listdir(data_dir) if f.endswith('.parquet')]
            if files:
                logger.info(f"Encontrados {len(files)} arquivos em {data_dir}")
                return data_dir, files
    return None, []

def load_existing_data(data_dir, files, target_gb=1.0):
    """Carrega dados já existentes"""
    dfs = []
    total_bytes = 0
    
    for file in files[:3]:  # Limitar a 3 arquivos para ser mais rápido
        filepath = os.path.join(data_dir, file)
        logger.info(f"Lendo {filepath}...")
        df = pd.read_parquet(filepath)
        dfs.append(df)
        total_bytes += df.memory_usage(deep=True).sum()
        logger.info(f"Tamanho acumulado: {total_bytes/1024/1024/1024:.2f} GB")
        if total_bytes >= target_gb * 1024**3:
            break
    
    if not dfs:
        raise Exception("Nenhum arquivo encontrado!")
    
    big_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Total final: {big_df.memory_usage(deep=True).sum()/1024/1024/1024:.2f} GB, {len(big_df)} linhas")
    return big_df

def convert_chunk_to_models_fast(df_chunk):
    """Conversão otimizada usando list comprehension"""
    instances = []
    
    # Preparar dados em lotes
    for i in range(0, len(df_chunk), 1000):  # Processar 1000 por vez
        sub_chunk = df_chunk.iloc[i:i+1000]
        
        chunk_instances = []
        for _, row in sub_chunk.iterrows():
            try:
                trip = RealTaxiTrip(
                    trip_id=uuid.uuid4(),
                    vendor_id=str(row.get('VendorID', 1)),
                    pickup_datetime=row.get('tpep_pickup_datetime'),
                    passenger_count=row.get('passenger_count', 1),
                    trip_distance=row.get('trip_distance', 0.0),
                    pickup_longitude=row.get('pickup_longitude', 0.0),
                    pickup_latitude=row.get('pickup_latitude', 0.0),
                    dropoff_longitude=row.get('dropoff_longitude', 0.0),
                    dropoff_latitude=row.get('dropoff_latitude', 0.0),
                    rate_code_id=row.get('RatecodeID', 1),
                    store_and_fwd_flag=str(row.get('store_and_fwd_flag', 'N')),
                    payment_type=row.get('payment_type', 1),
                    fare_amount=row.get('fare_amount', 0.0),
                    extra=row.get('extra', 0.0),
                    mta_tax=row.get('mta_tax', 0.0),
                    tip_amount=row.get('tip_amount', 0.0),
                    tolls_amount=row.get('tolls_amount', 0.0),
                    improvement_surcharge=row.get('improvement_surcharge', 0.0),
                    total_amount=row.get('total_amount', 0.0)
                )
                chunk_instances.append(trip)
            except Exception as e:
                continue
        
        instances.extend(chunk_instances)
        logger.info(f"  Sub-chunk {i//1000 + 1}: {len(chunk_instances)} instâncias criadas")
    
    return instances

def memory_usage_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def main():
    print("🚕 TESTE DE PERFORMANCE COM ~1GB DE DADOS REAIS NYC TLC - VERSÃO ULTRA-OTIMIZADA 🚕")
    
    # Conectar ao Cassandra
    connection.connect(contact_points=['localhost'], port=9042, keyspace=KEYSPACE)
    RealTaxiTrip.sync_table(auto_apply=True)
    print("✅ Conectado e schema sincronizado")

    # Procurar dados existentes
    data_dir, files = find_existing_data()
    if not data_dir:
        print("❌ Nenhum dado encontrado! Execute primeiro o script de download.")
        return
    
    print(f"📁 Usando dados de: {data_dir}")
    
    # Carregar dados
    df = load_existing_data(data_dir, files, target_gb=TARGET_SIZE_GB)
    
    # Processar e inserir em chunks grandes
    print(f"🚀 Processando {len(df)} linhas em chunks de {CHUNK_SIZE}...")
    total_processed = 0
    total_inserted = 0
    start_time = time.time()
    
    for i in range(0, len(df), CHUNK_SIZE):
        chunk_start = time.time()
        chunk = df.iloc[i:i+CHUNK_SIZE]
        
        print(f"📦 Processando chunk {i//CHUNK_SIZE + 1} ({len(chunk)} linhas)...")
        
        # Converter chunk para modelos
        conversion_start = time.time()
        instances = convert_chunk_to_models_fast(chunk)
        conversion_time = time.time() - conversion_start
        
        print(f"  ✅ Conversão: {len(instances)} instâncias em {conversion_time:.1f}s")
        
        # Inserir em batches maiores
        insertion_start = time.time()
        for j in range(0, len(instances), BATCH_SIZE):
            batch = instances[j:j+BATCH_SIZE]
            RealTaxiTrip.bulk_create(batch)
            total_inserted += len(batch)
        
        insertion_time = time.time() - insertion_start
        
        total_processed += len(chunk)
        chunk_time = time.time() - chunk_start
        
        print(f"  ✅ Inserção: {len(instances)} registros em {insertion_time:.1f}s")
        print(f"  📊 Progresso: {total_processed}/{len(df)} ({total_processed/len(df)*100:.1f}%)")
        print(f"  ⏱️  Chunk total: {chunk_time:.1f}s, Memória: {memory_usage_mb():.1f}MB")
        print(f"  🎯 Total inseridos: {total_inserted}")
        print("-" * 60)
    
    total_time = time.time() - start_time
    print(f"🎉 PROCESSAMENTO CONCLUÍDO!")
    print(f"📈 Total de registros processados: {total_processed}")
    print(f"📈 Total de registros inseridos: {total_inserted}")
    print(f"⏱️  Tempo total: {total_time/60:.2f} minutos")
    print(f"🚀 Registros por segundo: {total_inserted/total_time:.0f}")

if __name__ == "__main__":
    main() 