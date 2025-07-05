#!/usr/bin/env python3
"""
Teste de performance com dados reais do NYC TLC
Este script baixa e processa dados reais de táxi de Nova York para testar a CaspyORM
"""

import pytest
import time
import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from caspyorm import fields, Model, connection
import uuid
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealTaxiTrip(Model):
    """Modelo simplificado para dados reais do NYC TLC"""
    __table_name__ = 'real_nyc_taxi_trips'
    
    # Chaves primárias
    trip_id = fields.UUID(primary_key=True)
    vendor_id = fields.Text(partition_key=True)
    pickup_datetime = fields.Timestamp(clustering_key=True)
    
    # Dados básicos da viagem
    passenger_count = fields.Integer()
    trip_distance = fields.Float()
    pickup_longitude = fields.Float()
    pickup_latitude = fields.Float()
    dropoff_longitude = fields.Float()
    dropoff_latitude = fields.Float()
    
    # Informações de pagamento
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
    
    # Campos de auditoria
    created_at = fields.Timestamp(default=datetime.now)

class RealNYCDataTest:
    """Classe para testar com dados reais do NYC TLC"""
    
    def __init__(self):
        self.keyspace = 'nyc_taxi_real_test'
        self.data_dir = 'nyc_real_data'
        
        # Cria diretório se não existir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def connect(self):
        """Conecta ao Cassandra"""
        try:
            connection.connect(
                contact_points=['localhost'],
                port=9042,
                keyspace=self.keyspace
            )
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar: {e}")
            return False
    
    def sync_schema(self):
        """Sincroniza o schema da tabela"""
        try:
            RealTaxiTrip.sync_table(auto_apply=True)
            return True
        except Exception as e:
            logger.error(f"Erro ao sincronizar schema: {e}")
            return False
    
    def download_sample_data(self, sample_size=1000):
        """Baixa uma amostra de dados reais do NYC TLC"""
        try:
            # URL para dados de janeiro de 2024 (exemplo)
            url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
            filename = os.path.join(self.data_dir, "yellow_tripdata_2024-01.parquet")
            
            if not os.path.exists(filename):
                logger.info("Baixando dados reais do NYC TLC...")
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info("Download concluído!")
            else:
                logger.info("Arquivo já existe, usando cache...")
            
            # Lê apenas uma amostra
            df = pd.read_parquet(filename)
            df = df.head(sample_size)
            logger.info(f"Amostra carregada: {len(df)} registros")
            
            return df
            
        except Exception as e:
            logger.error(f"Erro ao baixar dados: {e}")
            return None
    
    def convert_to_model(self, df):
        """Converte DataFrame para instâncias do modelo"""
        instances = []
        
        for _, row in df.iterrows():
            try:
                # Mapeia colunas do TLC para nosso modelo
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
    
    def test_real_data_insertion(self, batch_sizes=[5, 10, 20]):
        """Testa inserção com dados reais"""
        print("\n=== TESTE COM DADOS REAIS DO NYC TLC ===")
        
        # Baixa dados reais
        df = self.download_sample_data(sample_size=100)
        if df is None:
            print("❌ Falha ao baixar dados reais")
            return False
        
        # Converte para modelo
        instances = self.convert_to_model(df)
        if not instances:
            print("❌ Nenhum registro válido encontrado")
            return False
        
        print(f"✅ {len(instances)} registros reais carregados")
        
        # Testa inserção em diferentes tamanhos de batch
        for batch_size in batch_sizes:
            print(f"\nTestando inserção de {batch_size} registros reais:")
            
            # Pega uma amostra do tamanho especificado
            batch_instances = instances[:batch_size]
            
            start_time = time.time()
            try:
                RealTaxiTrip.bulk_create(batch_instances)
                insert_time = time.time() - start_time
                
                print(f"  ✅ Inserção bem-sucedida")
                print(f"  Tempo: {insert_time:.2f}s")
                print(f"  Registros/s: {batch_size/insert_time:.0f}")
                
            except Exception as e:
                print(f"  ❌ Erro na inserção: {e}")
    
    def test_real_data_queries(self):
        """Testa consultas com dados reais"""
        print("\n=== TESTE DE CONSULTAS COM DADOS REAIS ===")
        
        # Teste 1: Contagem total
        print("\n1. Contagem total:")
        start_time = time.time()
        count = len(list(RealTaxiTrip.all()))
        query_time = time.time() - start_time
        print(f"  Total de registros: {count}")
        print(f"  Tempo: {query_time:.2f}s")
        
        # Teste 2: Filtro por vendor_id
        print("\n2. Filtro por vendor_id:")
        start_time = time.time()
        vendor_trips = list(RealTaxiTrip.filter(vendor_id="1"))
        query_time = time.time() - start_time
        print(f"  Registros encontrados: {len(vendor_trips)}")
        print(f"  Tempo: {query_time:.2f}s")
        
        # Teste 3: Filtro por valor de tarifa
        print("\n3. Filtro por tarifa alta (>$50):")
        start_time = time.time()
        # Como fare_amount não é indexado, vamos buscar todos e filtrar
        all_trips = list(RealTaxiTrip.all())
        expensive_trips = [trip for trip in all_trips if trip.fare_amount > 50]
        query_time = time.time() - start_time
        print(f"  Viagens caras encontradas: {len(expensive_trips)}")
        print(f"  Tempo: {query_time:.2f}s")
        
        if expensive_trips:
            avg_fare = sum(trip.fare_amount for trip in expensive_trips) / len(expensive_trips)
            print(f"  Tarifa média das viagens caras: ${avg_fare:.2f}")
    
    def run_all_tests(self):
        """Executa todos os testes com dados reais"""
        print("🚕 INICIANDO TESTES COM DADOS REAIS DO NYC TLC 🚕")
        
        if not self.connect():
            print("❌ Falha ao conectar ao Cassandra")
            return False
        
        if not self.sync_schema():
            print("❌ Falha ao sincronizar schema")
            return False
        
        print("✅ Conectado e schema sincronizado")
        
        try:
            self.test_real_data_insertion()
            self.test_real_data_queries()
            
            print("\n🎉 TESTES COM DADOS REAIS CONCLUÍDOS!")
            return True
            
        except Exception as e:
            print(f"❌ Erro durante os testes: {e}")
            return False

@pytest.mark.slow
def test_real_nyc_data():
    """Teste com dados reais do NYC TLC"""
    real_test = RealNYCDataTest()
    assert real_test.run_all_tests()

if __name__ == "__main__":
    real_test = RealNYCDataTest()
    real_test.run_all_tests() 