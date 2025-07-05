#!/usr/bin/env python3
"""
Teste de performance com ~1GB de dados reais do NYC TLC (yellow)
Baixa, concatena e insere dados em batches pequenos, registrando métricas.
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

class RealTaxiTrip(Model):
    __table_name__ = 'real_nyc_taxi_trips_1gb'
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

DATA_DIR = 'nyc_real_data_1gb'
KEYSPACE = 'nyc_taxi_real_1gb'
BATCH_SIZE = 10
TARGET_SIZE_GB = 1.0
YELLOW_URL_PATTERN = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month:02d}.parquet"

os.makedirs(DATA_DIR, exist_ok=True)

def download_files(years_months):
    files = []
    for year, month in years_months:
        url = YELLOW_URL_PATTERN.format(year=year, month=month)
        filename = os.path.join(DATA_DIR, f"yellow_tripdata_{year}-{month:02d}.parquet")
        if not os.path.exists(filename):
            logger.info(f"Baixando {filename}...")
            r = requests.get(url, stream=True)
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Download concluído: {filename}")
        else:
            logger.info(f"Arquivo já existe: {filename}")
        files.append(filename)
    return files

def load_and_concat(files, target_gb=1.0):
    dfs = []
    total_bytes = 0
    for file in files:
        logger.info(f"Lendo {file}...")
        df = pd.read_parquet(file)
        dfs.append(df)
        total_bytes += df.memory_usage(deep=True).sum()
        logger.info(f"Tamanho acumulado: {total_bytes/1024/1024/1024:.2f} GB")
        if total_bytes >= target_gb * 1024**3:
            break
    big_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Total final: {big_df.memory_usage(deep=True).sum()/1024/1024/1024:.2f} GB, {len(big_df)} linhas")
    return big_df

def convert_to_model(df):
    instances = []
    for _, row in df.iterrows():
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
            instances.append(trip)
        except Exception as e:
            logger.warning(f"Erro ao converter linha: {e}")
            continue
    logger.info(f"Convertidos {len(instances)} registros válidos")
    return instances

def memory_usage_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def main():
    print("🚕 TESTE DE PERFORMANCE COM ~1GB DE DADOS REAIS NYC TLC (YELLOW) 🚕")
    connection.connect(contact_points=['localhost'], port=9042, keyspace=KEYSPACE)
    RealTaxiTrip.sync_table(auto_apply=True)
    print("✅ Conectado e schema sincronizado")

    # Baixar arquivos de vários meses até atingir 1GB
    anos_meses = [(2024, m) for m in range(1, 7)] + [(2023, m) for m in range(12, 0, -1)]
    files = download_files(anos_meses)
    df = load_and_concat(files, target_gb=TARGET_SIZE_GB)

    # Converter para modelos
    print(f"Convertendo para instâncias CaspyORM...")
    instances = convert_to_model(df)
    print(f"Total de instâncias: {len(instances)}")

    # Inserir em batches pequenos
    print(f"Iniciando inserção em batches de {BATCH_SIZE}...")
    total = len(instances)
    start = time.time()
    for i in range(0, total, BATCH_SIZE):
        batch = instances[i:i+BATCH_SIZE]
        RealTaxiTrip.bulk_create(batch)
        if (i//BATCH_SIZE) % 100 == 0:
            print(f"{i+len(batch)}/{total} inseridos... Memória: {memory_usage_mb():.2f}MB")
    elapsed = time.time() - start
    print(f"✅ Inserção concluída de {total} registros em {elapsed/60:.2f} minutos")
    print(f"Registros por segundo: {total/elapsed:.0f}")

if __name__ == "__main__":
    main() 