#!/usr/bin/env python3
"""
Teste de performance com dados reais do NYC TLC - VERSÃO LIMPA
Baixa apenas 1 arquivo (~200-500MB) para teste rápido e eficiente.
"""

import os
import time
import requests
import pandas as pd
from datetime import datetime
from caspyorm import fields, Model, connection
import uuid
import logging
import psutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaxiTrip(Model):
    __table_name__ = 'nyc_taxi_clean'
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

DATA_DIR = 'nyc_clean_data'
KEYSPACE = 'nyc_taxi_clean'
BATCH_SIZE = 50
CHUNK_SIZE = 10000
URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"

os.makedirs(DATA_DIR, exist_ok=True)

def download_single_file():
    """Baixa apenas 1 arquivo do NYC TLC"""
    filename = os.path.join(DATA_DIR, "yellow_tripdata_2024-01.parquet")
    
    if not os.path.exists(filename):
        logger.info("Baixando arquivo único do NYC TLC...")
        response = requests.get(URL, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info("Download concluído!")
    else:
        logger.info("Arquivo já existe, usando cache...")
    
    return filename

def load_and_limit_data(filename, max_rows=100000):
    """Carrega e limita os dados"""
    logger.info(f"Carregando dados (limitado a {max_rows} linhas)...")
    df = pd.read_parquet(filename)
    
    # Limita o número de linhas
    if len(df) > max_rows:
        df = df.head(max_rows)
        logger.info(f"Limitado a {max_rows} linhas")
    
    size_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
    logger.info(f"Dados carregados: {len(df)} linhas, {size_mb:.1f} MB")
    
    return df

def convert_chunk_fast(df_chunk):
    """Conversão rápida de chunk"""
    instances = []
    for _, row in df_chunk.iterrows():
        try:
            trip = TaxiTrip(
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
            instances.append(trip)
        except Exception as e:
            continue
    
    return instances

def memory_usage_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def main():
    print("🚕 TESTE DE PERFORMANCE NYC TLC - VERSÃO LIMPA E RÁPIDA 🚕")
    
    # Conectar ao Cassandra
    connection.connect(contact_points=['localhost'], port=9042, keyspace=KEYSPACE)
    TaxiTrip.sync_table(auto_apply=True)
    print("✅ Conectado e schema sincronizado")

    # Baixar e carregar dados
    filename = download_single_file()
    df = load_and_limit_data(filename, max_rows=100000)  # Limita a 100k linhas
    
    # Processar e inserir
    print(f"🚀 Processando {len(df)} linhas em chunks de {CHUNK_SIZE}...")
    total_processed = 0
    total_inserted = 0
    start_time = time.time()
    
    for i in range(0, len(df), CHUNK_SIZE):
        chunk_start = time.time()
        chunk = df.iloc[i:i+CHUNK_SIZE]
        
        print(f"📦 Chunk {i//CHUNK_SIZE + 1}: {len(chunk)} linhas...")
        
        # Converter
        instances = convert_chunk_fast(chunk)
        
        # Inserir
        for j in range(0, len(instances), BATCH_SIZE):
            batch = instances[j:j+BATCH_SIZE]
            TaxiTrip.bulk_create(batch)
            total_inserted += len(batch)
        
        total_processed += len(chunk)
        chunk_time = time.time() - chunk_start
        
        print(f"  ✅ {len(instances)} inseridos em {chunk_time:.1f}s")
        print(f"  📊 Progresso: {total_processed}/{len(df)} ({total_processed/len(df)*100:.1f}%)")
        print(f"  🎯 Total: {total_inserted}, Memória: {memory_usage_mb():.1f}MB")
        print("-" * 50)
    
    total_time = time.time() - start_time
    print(f"🎉 CONCLUÍDO!")
    print(f"📈 Registros processados: {total_processed}")
    print(f"📈 Registros inseridos: {total_inserted}")
    print(f"⏱️  Tempo total: {total_time/60:.2f} minutos")
    print(f"🚀 Registros/segundo: {total_inserted/total_time:.0f}")

if __name__ == "__main__":
    main() 