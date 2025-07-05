#!/usr/bin/env python3
"""
Script de benchmark para testar CaspyORM com dados reais de táxi de Nova York
Compara performance com diferentes volumes de dados e operações
"""

import time
import psutil
import os
import json
import csv
from datetime import datetime, timedelta
from caspyorm import fields, Model, connection
from caspyorm.exceptions import ConnectionError
import uuid
import random
from typing import List, Dict, Any
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaxiTrip(Model):
    """Modelo para dados de táxi de Nova York"""
    __table_name__ = 'nyc_taxi_trips_benchmark'
    
    trip_id = fields.UUID(primary_key=True)
    vendor_id = fields.Text(partition_key=True)
    pickup_datetime = fields.DateTime(clustering_key=True)
    dropoff_datetime = fields.DateTime(clustering_key=True)
    
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
    congestion_surcharge = fields.Float()
    
    pickup_location = fields.Text(index=True)
    dropoff_location = fields.Text(index=True)
    trip_tags = fields.List(fields.Text())
    trip_features = fields.Set(fields.Text())
    trip_metadata = fields.Map(fields.Text(), fields.Text())
    
    created_at = fields.DateTime(default=datetime.utcnow)
    updated_at = fields.DateTime(default=datetime.utcnow)

class BenchmarkResult:
    """Classe para armazenar resultados de benchmark"""
    
    def __init__(self, test_name: str, data_size: int):
        self.test_name = test_name
        self.data_size = data_size
        self.start_time = None
        self.end_time = None
        self.memory_before = None
        self.memory_after = None
        self.records_processed = 0
        self.error = None
    
    def start(self):
        """Inicia o benchmark"""
        self.start_time = time.time()
        self.memory_before = self.measure_memory()
    
    def end(self, records_processed: int = 0):
        """Finaliza o benchmark"""
        self.end_time = time.time()
        self.memory_after = self.measure_memory()
        self.records_processed = records_processed
    
    def set_error(self, error: str):
        """Define erro no benchmark"""
        self.error = error
    
    def measure_memory(self) -> float:
        """Mede uso de memória em MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    @property
    def duration(self) -> float:
        """Retorna duração em segundos"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
    
    @property
    def memory_used(self) -> float:
        """Retorna memória utilizada em MB"""
        if self.memory_before and self.memory_after:
            return self.memory_after - self.memory_before
        return 0
    
    @property
    def records_per_second(self) -> float:
        """Retorna registros processados por segundo"""
        if self.duration > 0 and self.records_processed > 0:
            return self.records_processed / self.duration
        return 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'test_name': self.test_name,
            'data_size': self.data_size,
            'duration': self.duration,
            'memory_used': self.memory_used,
            'records_processed': self.records_processed,
            'records_per_second': self.records_per_second,
            'error': self.error,
            'timestamp': datetime.utcnow().isoformat()
        }

class NYCTaxiBenchmark:
    """Classe principal para executar benchmarks"""
    
    def __init__(self, cassandra_host='localhost', cassandra_port=9042):
        self.cassandra_host = cassandra_host
        self.cassandra_port = cassandra_port
        self.keyspace = 'nyc_taxi_benchmark'
        self.connection = None
        self.results = []
        
    def connect(self) -> bool:
        """Conecta ao Cassandra"""
        try:
            self.connection = connection.Connection(
                hosts=[self.cassandra_host],
                port=self.cassandra_port,
                keyspace=self.keyspace
            )
            return True
        except ConnectionError as e:
            logger.error(f"Erro ao conectar: {e}")
            return False
    
    def setup_database(self) -> bool:
        """Configura banco de dados"""
        try:
            session = self.connection.get_session()
            session.execute(f"""
                CREATE KEYSPACE IF NOT EXISTS {self.keyspace}
                WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
            """)
            session.execute(f"USE {self.keyspace}")
            
            TaxiTrip.sync_schema(self.connection)
            return True
        except Exception as e:
            logger.error(f"Erro ao configurar banco: {e}")
            return False
    
    def generate_test_data(self, num_records: int) -> List[TaxiTrip]:
        """Gera dados de teste"""
        data = []
        
        pickup_zones = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
        dropoff_zones = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
        trip_tags_options = ["rush_hour", "late_night", "airport", "bridge_tunnel", "highway"]
        trip_features_options = ["long_distance", "short_trip", "high_fare", "low_fare", "tipped"]
        
        base_time = datetime(2024, 1, 1)
        
        for i in range(num_records):
            random_hours = random.randint(0, 24*365)
            pickup_time = base_time + timedelta(hours=random_hours)
            trip_duration = random.randint(5, 120)
            dropoff_time = pickup_time + timedelta(minutes=trip_duration)
            
            pickup_lat = random.uniform(40.5, 40.9)
            pickup_lon = random.uniform(-74.3, -73.7)
            dropoff_lat = random.uniform(40.5, 40.9)
            dropoff_lon = random.uniform(-74.3, -73.7)
            
            trip_distance = random.uniform(0.1, 50.0)
            fare_amount = 2.50 + (trip_distance * 2.50)
            tip_amount = fare_amount * random.uniform(0, 0.3)
            total_amount = fare_amount + tip_amount + random.uniform(0, 5)
            
            num_tags = random.randint(1, 3)
            trip_tags = random.sample(trip_tags_options, num_tags)
            
            num_features = random.randint(1, 3)
            trip_features = set(random.sample(trip_features_options, num_features))
            
            trip_metadata = {
                "weather": random.choice(["sunny", "rainy", "snowy", "cloudy"]),
                "traffic": random.choice(["light", "moderate", "heavy"]),
                "driver_rating": str(random.uniform(3.0, 5.0))
            }
            
            trip = TaxiTrip(
                trip_id=uuid.uuid4(),
                vendor_id=str(random.randint(1, 2)),
                pickup_datetime=pickup_time,
                dropoff_datetime=dropoff_time,
                passenger_count=random.randint(1, 6),
                trip_distance=trip_distance,
                pickup_longitude=pickup_lon,
                pickup_latitude=pickup_lat,
                dropoff_longitude=dropoff_lon,
                dropoff_latitude=dropoff_lat,
                rate_code_id=random.randint(1, 6),
                store_and_fwd_flag=random.choice(["Y", "N"]),
                payment_type=random.randint(1, 6),
                fare_amount=fare_amount,
                extra=random.uniform(0, 2),
                mta_tax=0.50,
                tip_amount=tip_amount,
                tolls_amount=random.uniform(0, 10),
                improvement_surcharge=0.30,
                total_amount=total_amount,
                congestion_surcharge=random.uniform(0, 5),
                pickup_location=random.choice(pickup_zones),
                dropoff_location=random.choice(dropoff_zones),
                trip_tags=trip_tags,
                trip_features=trip_features,
                trip_metadata=trip_metadata
            )
            
            data.append(trip)
        
        return data
    
    def benchmark_batch_insert(self, data_sizes: List[int]) -> None:
        """Benchmark de inserção em lote"""
        logger.info("=== BENCHMARK DE INSERÇÃO EM LOTE ===")
        
        for size in data_sizes:
            result = BenchmarkResult(f"batch_insert_{size}", size)
            
            try:
                logger.info(f"Testando inserção de {size} registros...")
                
                # Gera dados
                result.start()
                data = self.generate_test_data(size)
                generation_time = time.time() - result.start_time
                
                # Insere em lote
                TaxiTrip.insert_batch(data, self.connection)
                result.end(size)
                
                logger.info(f"  Geração: {generation_time:.2f}s")
                logger.info(f"  Inserção: {result.duration:.2f}s")
                logger.info(f"  Total: {generation_time + result.duration:.2f}s")
                logger.info(f"  Registros/s: {result.records_per_second:.0f}")
                logger.info(f"  Memória: {result.memory_used:.2f}MB")
                
            except Exception as e:
                result.set_error(str(e))
                logger.error(f"Erro no teste de {size} registros: {e}")
            
            self.results.append(result)
    
    def benchmark_queries(self, data_sizes: List[int]) -> None:
        """Benchmark de consultas"""
        logger.info("=== BENCHMARK DE CONSULTAS ===")
        
        for size in data_sizes:
            # Primeiro insere dados para teste
            data = self.generate_test_data(size)
            TaxiTrip.insert_batch(data, self.connection)
            
            # Teste 1: Contagem
            result = BenchmarkResult(f"count_{size}", size)
            try:
                result.start()
                count = TaxiTrip.objects(self.connection).count()
                result.end(count)
                logger.info(f"Count {size}: {result.duration:.2f}s ({count} registros)")
            except Exception as e:
                result.set_error(str(e))
            self.results.append(result)
            
            # Teste 2: Consulta por vendor_id
            result = BenchmarkResult(f"filter_vendor_{size}", size)
            try:
                result.start()
                trips = list(TaxiTrip.objects(self.connection).filter(vendor_id="1").limit(1000))
                result.end(len(trips))
                logger.info(f"Filter vendor {size}: {result.duration:.2f}s ({len(trips)} registros)")
            except Exception as e:
                result.set_error(str(e))
            self.results.append(result)
            
            # Teste 3: Consulta por data
            result = BenchmarkResult(f"filter_date_{size}", size)
            try:
                seven_days_ago = datetime.utcnow() - timedelta(days=7)
                result.start()
                trips = list(TaxiTrip.objects(self.connection).filter(
                    pickup_datetime__gte=seven_days_ago
                ).limit(1000))
                result.end(len(trips))
                logger.info(f"Filter date {size}: {result.duration:.2f}s ({len(trips)} registros)")
            except Exception as e:
                result.set_error(str(e))
            self.results.append(result)
    
    def benchmark_export(self, data_sizes: List[int]) -> None:
        """Benchmark de exportação"""
        logger.info("=== BENCHMARK DE EXPORTAÇÃO ===")
        
        for size in data_sizes:
            # Insere dados para teste
            data = self.generate_test_data(size)
            TaxiTrip.insert_batch(data, self.connection)
            
            # Teste de exportação JSON
            result = BenchmarkResult(f"export_json_{size}", size)
            try:
                result.start()
                trips = TaxiTrip.objects(self.connection).limit(size)
                json_data = []
                for trip in trips:
                    json_data.append(trip.to_dict())
                result.end(len(json_data))
                logger.info(f"Export JSON {size}: {result.duration:.2f}s ({len(json_data)} registros)")
            except Exception as e:
                result.set_error(str(e))
            self.results.append(result)
    
    def save_results(self, filename: str = "benchmark_results.json") -> None:
        """Salva resultados em arquivo"""
        try:
            results_dict = [result.to_dict() for result in self.results]
            
            with open(filename, 'w') as f:
                json.dump(results_dict, f, indent=2, default=str)
            
            logger.info(f"Resultados salvos em: {filename}")
            
            # Também salva como CSV
            csv_filename = filename.replace('.json', '.csv')
            with open(csv_filename, 'w', newline='') as f:
                if results_dict:
                    writer = csv.DictWriter(f, fieldnames=results_dict[0].keys())
                    writer.writeheader()
                    writer.writerows(results_dict)
            
            logger.info(f"Resultados CSV salvos em: {csv_filename}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar resultados: {e}")
    
    def print_summary(self) -> None:
        """Imprime resumo dos resultados"""
        print("\n" + "="*60)
        print("📊 RESUMO DOS BENCHMARKS")
        print("="*60)
        
        for result in self.results:
            if result.error:
                print(f"❌ {result.test_name}: ERRO - {result.error}")
            else:
                print(f"✅ {result.test_name}: {result.duration:.2f}s, "
                      f"{result.records_per_second:.0f} reg/s, "
                      f"{result.memory_used:.2f}MB")
    
    def run_full_benchmark(self) -> bool:
        """Executa benchmark completo"""
        logger.info("🚕 INICIANDO BENCHMARK COMPLETO DE TÁXI NYC 🚕")
        
        if not self.connect():
            logger.error("❌ Falha ao conectar ao Cassandra")
            return False
        
        if not self.setup_database():
            logger.error("❌ Falha ao configurar banco de dados")
            return False
        
        logger.info("✅ Banco de dados configurado")
        
        # Define tamanhos de dados para teste
        data_sizes = [100, 1000, 10000, 100000]  # Ajuste conforme necessário
        
        try:
            # Executa benchmarks
            self.benchmark_batch_insert(data_sizes)
            self.benchmark_queries(data_sizes)
            self.benchmark_export(data_sizes)
            
            # Salva e exibe resultados
            self.save_results()
            self.print_summary()
            
            logger.info("🎉 BENCHMARK CONCLUÍDO COM SUCESSO!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro durante benchmark: {e}")
            return False

def main():
    """Função principal"""
    benchmark = NYCTaxiBenchmark()
    success = benchmark.run_full_benchmark()
    
    if success:
        print("\n✅ Benchmark executado com sucesso!")
        print("📁 Verifique os arquivos de resultado gerados")
    else:
        print("\n❌ Falha no benchmark")

if __name__ == "__main__":
    main() 