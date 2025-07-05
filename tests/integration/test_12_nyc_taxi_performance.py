import pytest
import time
import psutil
import os
from datetime import datetime, timedelta
from caspyorm import fields, Model, connection
from caspyorm.exceptions import ConnectionError
import uuid
import random
import json

# Modelo para dados de táxi de Nova York baseado na estrutura TLC
class TaxiTrip(Model):
    __table_name__ = 'nyc_taxi_trips'
    
    # Chaves primárias
    trip_id = fields.UUID(primary_key=True)
    vendor_id = fields.Text(partition_key=True)  # 1=Creative Mobile Technologies, 2=VeriFone Inc.
    
    # Clustering keys para otimizar consultas por data/hora
    pickup_datetime = fields.Timestamp(clustering_key=True)
    dropoff_datetime = fields.Timestamp(clustering_key=True)
    
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
    congestion_surcharge = fields.Float()
    
    # Campos complexos para testar performance
    pickup_location = fields.Text(index=True)
    dropoff_location = fields.Text(index=True)
    
    # Lista de tags para testar collections
    trip_tags = fields.List(fields.Text())
    
    # Set de características da viagem
    trip_features = fields.Set(fields.Text())
    
    # Map de metadados adicionais
    trip_metadata = fields.Map(fields.Text(), fields.Text())
    
    # Campos de auditoria
    created_at = fields.Timestamp(default=datetime.utcnow)
    updated_at = fields.Timestamp(default=datetime.utcnow)

class TaxiPerformanceTest:
    """Classe para executar testes de performance com dados de táxi"""
    
    def __init__(self, cassandra_host='localhost', cassandra_port=9042):
        self.cassandra_host = cassandra_host
        self.cassandra_port = cassandra_port
        self.keyspace = 'nyc_taxi_test'
        
    def connect(self):
        """Conecta ao Cassandra"""
        try:
            connection.connect(
                contact_points=[self.cassandra_host],
                port=self.cassandra_port,
                keyspace=self.keyspace
            )
            return True
        except Exception as e:
            print(f"Erro ao conectar: {e}")
            return False
    
    def create_keyspace(self):
        """Cria o keyspace de teste"""
        try:
            # O keyspace é criado automaticamente na conexão
            return True
        except Exception as e:
            print(f"Erro ao criar keyspace: {e}")
            return False
    
    def sync_schema(self):
        """Sincroniza o schema da tabela"""
        try:
            TaxiTrip.sync_table(auto_apply=True)
            return True
        except Exception as e:
            print(f"Erro ao sincronizar schema: {e}")
            return False
    
    def generate_sample_data(self, num_records=1000):
        """Gera dados de exemplo para teste"""
        data = []
        
        # Zonas de táxi de NYC (simplificadas)
        pickup_zones = [
            "Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island",
            "JFK Airport", "LaGuardia Airport", "Newark Airport"
        ]
        
        dropoff_zones = [
            "Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island",
            "JFK Airport", "LaGuardia Airport", "Newark Airport"
        ]
        
        # Tags possíveis
        trip_tags_options = [
            "rush_hour", "late_night", "airport", "bridge_tunnel", 
            "highway", "downtown", "uptown", "weekend", "holiday"
        ]
        
        # Features possíveis
        trip_features_options = [
            "long_distance", "short_trip", "high_fare", "low_fare",
            "tipped", "no_tip", "cash_payment", "card_payment"
        ]
        
        base_time = datetime(2024, 1, 1)
        
        for i in range(num_records):
            # Gera data/hora aleatória
            random_hours = random.randint(0, 24*365)  # 1 ano de dados
            pickup_time = base_time + timedelta(hours=random_hours)
            trip_duration = random.randint(5, 120)  # 5-120 minutos
            dropoff_time = pickup_time + timedelta(minutes=trip_duration)
            
            # Gera coordenadas aleatórias (aproximadamente NYC)
            pickup_lat = random.uniform(40.5, 40.9)
            pickup_lon = random.uniform(-74.3, -73.7)
            dropoff_lat = random.uniform(40.5, 40.9)
            dropoff_lon = random.uniform(-74.3, -73.7)
            
            # Calcula distância aproximada
            trip_distance = random.uniform(0.1, 50.0)
            
            # Calcula valores de tarifa
            base_fare = 2.50
            fare_per_mile = 2.50
            fare_amount = base_fare + (trip_distance * fare_per_mile)
            tip_amount = fare_amount * random.uniform(0, 0.3)
            total_amount = fare_amount + tip_amount + random.uniform(0, 5)
            
            # Gera tags e features aleatórias
            num_tags = random.randint(1, 4)
            trip_tags = random.sample(trip_tags_options, num_tags)
            
            num_features = random.randint(1, 3)
            trip_features = set(random.sample(trip_features_options, num_features))
            
            # Metadados adicionais
            trip_metadata = {
                "weather": random.choice(["sunny", "rainy", "snowy", "cloudy"]),
                "traffic": random.choice(["light", "moderate", "heavy"]),
                "driver_rating": str(random.uniform(3.0, 5.0)),
                "vehicle_type": random.choice(["sedan", "suv", "hybrid", "electric"])
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
    
    def measure_memory_usage(self):
        """Mede o uso de memória atual"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB
    
    def test_batch_insert_performance(self, batch_sizes=[10, 20, 30]):
        """Testa performance de inserção em lote"""
        print("\n=== TESTE DE PERFORMANCE DE INSERÇÃO EM LOTE ===")
        
        for batch_size in batch_sizes:
            print(f"\nTestando inserção em lote de {batch_size} registros:")
            
            # Gera dados
            start_time = time.time()
            data = self.generate_sample_data(batch_size)
            generation_time = time.time() - start_time
            print(f"  Tempo para gerar dados: {generation_time:.2f}s")
            
            # Mede memória antes
            memory_before = self.measure_memory_usage()
            
            # Insere em lote
            start_time = time.time()
            TaxiTrip.bulk_create(data)
            insert_time = time.time() - start_time
            
            # Mede memória depois
            memory_after = self.measure_memory_usage()
            memory_used = memory_after - memory_before
            
            print(f"  Tempo de inserção: {insert_time:.2f}s")
            print(f"  Registros por segundo: {batch_size/insert_time:.0f}")
            print(f"  Memória utilizada: {memory_used:.2f}MB")
            print(f"  Total de tempo: {generation_time + insert_time:.2f}s")
    
    def test_query_performance(self):
        """Testa performance de consultas"""
        print("\n=== TESTE DE PERFORMANCE DE CONSULTAS ===")
        
        # Teste 1: Contagem total
        print("\n1. Contagem total de registros:")
        start_time = time.time()
        # Como não há método count() direto, vamos usar filter() e contar
        all_trips = list(TaxiTrip.all())
        count = len(all_trips)
        query_time = time.time() - start_time
        print(f"  Total de registros: {count}")
        print(f"  Tempo de consulta: {query_time:.2f}s")
        
        # Teste 2: Consulta por vendor_id
        print("\n2. Consulta por vendor_id:")
        start_time = time.time()
        vendor_trips = list(TaxiTrip.filter(vendor_id="1"))
        query_time = time.time() - start_time
        print(f"  Registros encontrados: {len(vendor_trips)}")
        print(f"  Tempo de consulta: {query_time:.2f}s")
        
        # Teste 3: Consulta por data
        print("\n3. Consulta por data (últimos 7 dias):")
        seven_days_ago = datetime.now() - timedelta(days=7)
        start_time = time.time()
        recent_trips = list(TaxiTrip.filter(pickup_datetime__gte=seven_days_ago))
        query_time = time.time() - start_time
        print(f"  Registros encontrados: {len(recent_trips)}")
        print(f"  Tempo de consulta: {query_time:.2f}s")
        
        # Teste 4: Consulta com filtro em lista
        print("\n4. Consulta com filtro em lista (trip_tags):")
        start_time = time.time()
        # Como não há filtro direto em lista, vamos buscar todos e filtrar
        all_trips = list(TaxiTrip.all())
        airport_trips = [trip for trip in all_trips if "airport" in trip.trip_tags]
        query_time = time.time() - start_time
        print(f"  Registros encontrados: {len(airport_trips)}")
        print(f"  Tempo de consulta: {query_time:.2f}s")
    
    def test_export_performance(self):
        """Testa performance de exportação"""
        print("\n=== TESTE DE PERFORMANCE DE EXPORTAÇÃO ===")
        
        # Teste 1: Exportação para JSON
        print("\n1. Exportação para JSON:")
        start_time = time.time()
        trips = list(TaxiTrip.all())
        json_data = []
        for trip in trips:
            json_data.append(trip.model_dump())
        
        export_time = time.time() - start_time
        print(f"  Registros exportados: {len(json_data)}")
        print(f"  Tempo de exportação: {export_time:.2f}s")
        print(f"  Registros por segundo: {len(json_data)/export_time:.0f}")
        
        # Salva arquivo JSON
        with open('taxi_trips_export.json', 'w') as f:
            json.dump(json_data, f, default=str)
        print(f"  Arquivo salvo: taxi_trips_export.json")
    
    def test_complex_queries(self):
        """Testa consultas complexas"""
        print("\n=== TESTE DE CONSULTAS COMPLEXAS ===")
        
        # Teste 1: Múltiplos filtros
        print("\n1. Múltiplos filtros:")
        start_time = time.time()
        complex_query = list(TaxiTrip.filter(
            vendor_id="1",
            passenger_count__gte=2,
            fare_amount__gte=10.0
        ))
        query_time = time.time() - start_time
        print(f"  Registros encontrados: {len(complex_query)}")
        print(f"  Tempo de consulta: {query_time:.2f}s")
        
        # Teste 2: Filtro em Map
        print("\n2. Filtro em Map (trip_metadata):")
        start_time = time.time()
        # Buscar todos e filtrar em memória
        all_trips = list(TaxiTrip.all())
        filtered_trips = []
        for trip in all_trips:
            if trip.trip_metadata.get('weather') == 'sunny':
                filtered_trips.append(trip)
        query_time = time.time() - start_time
        print(f"  Registros encontrados: {len(filtered_trips)}")
        print(f"  Tempo de consulta: {query_time:.2f}s")
    
    def run_all_tests(self):
        """Executa todos os testes de performance"""
        print("🚕 INICIANDO TESTES DE PERFORMANCE COM DADOS DE TÁXI NYC 🚕")
        
        if not self.connect():
            print("❌ Falha ao conectar ao Cassandra")
            return False
        
        if not self.create_keyspace():
            print("❌ Falha ao criar keyspace")
            return False
        
        if not self.sync_schema():
            print("❌ Falha ao sincronizar schema")
            return False
        
        print("✅ Conectado e schema sincronizado")
        
        try:
            self.test_batch_insert_performance()
            self.test_query_performance()
            self.test_export_performance()
            self.test_complex_queries()
            
            print("\n🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
            return True
            
        except Exception as e:
            print(f"❌ Erro durante os testes: {e}")
            return False

@pytest.mark.slow
def test_nyc_taxi_performance():
    """Teste de performance com dados de táxi de Nova York"""
    performance_test = TaxiPerformanceTest()
    assert performance_test.run_all_tests()

if __name__ == "__main__":
    # Execução direta para desenvolvimento
    performance_test = TaxiPerformanceTest()
    performance_test.run_all_tests() 