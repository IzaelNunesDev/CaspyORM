#!/usr/bin/env python3
"""
Script de benchmark automatizado para CaspyORM.
Gera métricas de performance em formato JSON para comparação de regressões.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any
import statistics
import argparse
import sys
import os

# Adicionar o diretório raiz ao path para importar caspyorm
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from caspyorm import Model, connect, connect_async
from caspyorm.fields import Text, Integer, UUID, Timestamp, List as ListField, Set as SetField
from caspyorm.exceptions import ValidationError

class BenchmarkModel(Model):
    """Modelo para testes de benchmark."""
    id = UUID(primary_key=True)
    name = Text(required=True)
    email = Text(index=True)
    age = Integer()
    created_at = Timestamp(default=datetime.now)
    tags = ListField(Text())
    scores = SetField(Integer())

class BenchmarkResults:
    """Classe para armazenar e calcular resultados de benchmark."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "version": "0.1.0",
            "metrics": {}
        }
    
    def add_metric(self, name: str, value: float, unit: str = "ms"):
        """Adiciona uma métrica aos resultados."""
        if name not in self.results["metrics"]:
            self.results["metrics"][name] = []
        
        self.results["metrics"][name].append({
            "value": value,
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_batch_metric(self, name: str, values: List[float], unit: str = "ms"):
        """Adiciona métricas em lote com estatísticas."""
        if values:
            self.results["metrics"][name] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "std": statistics.stdev(values) if len(values) > 1 else 0,
                "unit": unit,
                "values": values,
                "timestamp": datetime.now().isoformat()
            }
    
    def save_to_file(self, filename: str):
        """Salva os resultados em arquivo JSON."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
    
    def print_summary(self):
        """Imprime um resumo dos resultados."""
        print("\n" + "="*60)
        print("RESULTADOS DO BENCHMARK")
        print("="*60)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Versão: {self.results['version']}")
        print()
        
        for metric_name, metric_data in self.results["metrics"].items():
            if isinstance(metric_data, list):
                # Métrica simples
                latest = metric_data[-1]
                print(f"{metric_name}: {latest['value']:.2f} {latest['unit']}")
            else:
                # Métrica com estatísticas
                print(f"{metric_name}:")
                print(f"  Média: {metric_data['mean']:.2f} {metric_data['unit']}")
                print(f"  Mediana: {metric_data['median']:.2f} {metric_data['unit']}")
                print(f"  Min: {metric_data['min']:.2f} {metric_data['unit']}")
                print(f"  Max: {metric_data['max']:.2f} {metric_data['unit']}")
                print(f"  Std: {metric_data['std']:.2f} {metric_data['unit']}")
                print(f"  Count: {metric_data['count']}")
            print()

class BenchmarkRunner:
    """Executor de benchmarks."""
    
    def __init__(self, contact_points: List[str] = None, keyspace: str = "benchmark_keyspace"):
        self.contact_points = contact_points or ['localhost']
        self.keyspace = keyspace
        self.results = BenchmarkResults()
        
    def setup(self):
        """Configura o ambiente de benchmark."""
        print("🔧 Configurando ambiente de benchmark...")
        
        # Conectar ao Cassandra
        connect(contact_points=self.contact_points, keyspace=self.keyspace)
        
        # Sincronizar tabela
        BenchmarkModel.sync_table(auto_apply=True)
        
        print("✅ Ambiente configurado!")
    
    async def setup_async(self):
        """Configura o ambiente de benchmark (assíncrono)."""
        print("🔧 Configurando ambiente de benchmark (assíncrono)...")
        
        # Conectar ao Cassandra
        await connect_async(contact_points=self.contact_points, keyspace=self.keyspace)
        
        # Sincronizar tabela
        await BenchmarkModel.sync_table_async(auto_apply=True)
        
        print("✅ Ambiente configurado (assíncrono)!")
    
    def benchmark_single_insert(self, iterations: int = 1000):
        """Benchmark de inserção única."""
        print(f"📊 Executando benchmark de inserção única ({iterations} iterações)...")
        
        times = []
        
        for i in range(iterations):
            start_time = time.time()
            
            user = BenchmarkModel(
                id=uuid.uuid4(),
                name=f"User {i}",
                email=f"user{i}@example.com",
                age=20 + (i % 50),
                tags=[f"tag{i}", f"category{i%10}"],
                scores={i, i+1, i+2}
            )
            user.save()
            
            end_time = time.time()
            times.append((end_time - start_time) * 1000)  # Converter para ms
        
        # Calcular métricas
        self.results.add_batch_metric("single_insert_latency", times, "ms")
        self.results.add_metric("single_insert_throughput", iterations / (sum(times) / 1000), "ops/s")
        
        print(f"✅ Inserção única: {statistics.mean(times):.2f}ms (média)")
    
    async def benchmark_single_insert_async(self, iterations: int = 1000):
        """Benchmark de inserção única (assíncrono)."""
        print(f"📊 Executando benchmark de inserção única assíncrona ({iterations} iterações)...")
        
        times = []
        
        for i in range(iterations):
            start_time = time.time()
            
            user = BenchmarkModel(
                id=uuid.uuid4(),
                name=f"User {i}",
                email=f"user{i}@example.com",
                age=20 + (i % 50),
                tags=[f"tag{i}", f"category{i%10}"],
                scores={i, i+1, i+2}
            )
            await user.save_async()
            
            end_time = time.time()
            times.append((end_time - start_time) * 1000)  # Converter para ms
        
        # Calcular métricas
        self.results.add_batch_metric("single_insert_async_latency", times, "ms")
        self.results.add_metric("single_insert_async_throughput", iterations / (sum(times) / 1000), "ops/s")
        
        print(f"✅ Inserção única assíncrona: {statistics.mean(times):.2f}ms (média)")
    
    def benchmark_bulk_insert(self, batch_sizes: List[int] = [10, 100, 1000]):
        """Benchmark de inserção em lote."""
        print("📊 Executando benchmark de inserção em lote...")
        
        for batch_size in batch_sizes:
            print(f"  Testando batch de {batch_size} registros...")
            
            # Criar instâncias
            instances = []
            for i in range(batch_size):
                user = BenchmarkModel(
                    id=uuid.uuid4(),
                    name=f"BulkUser {i}",
                    email=f"bulk{i}@example.com",
                    age=20 + (i % 50),
                    tags=[f"bulk{i}", f"category{i%10}"],
                    scores={i, i+1, i+2}
                )
                instances.append(user)
            
            # Medir tempo de inserção em lote
            start_time = time.time()
            BenchmarkModel.bulk_create(instances)
            end_time = time.time()
            
            total_time = (end_time - start_time) * 1000  # ms
            throughput = batch_size / (total_time / 1000)  # ops/s
            
            self.results.add_metric(f"bulk_insert_{batch_size}_latency", total_time, "ms")
            self.results.add_metric(f"bulk_insert_{batch_size}_throughput", throughput, "ops/s")
            
            print(f"    ✅ {batch_size} registros: {total_time:.2f}ms ({throughput:.0f} ops/s)")
    
    async def benchmark_bulk_insert_async(self, batch_sizes: List[int] = [10, 100, 1000]):
        """Benchmark de inserção em lote (assíncrono)."""
        print("📊 Executando benchmark de inserção em lote assíncrona...")
        
        for batch_size in batch_sizes:
            print(f"  Testando batch assíncrono de {batch_size} registros...")
            
            # Criar instâncias
            instances = []
            for i in range(batch_size):
                user = BenchmarkModel(
                    id=uuid.uuid4(),
                    name=f"AsyncBulkUser {i}",
                    email=f"asyncbulk{i}@example.com",
                    age=20 + (i % 50),
                    tags=[f"async{i}", f"category{i%10}"],
                    scores={i, i+1, i+2}
                )
                instances.append(user)
            
            # Medir tempo de inserção em lote
            start_time = time.time()
            await BenchmarkModel.bulk_create_async(instances)
            end_time = time.time()
            
            total_time = (end_time - start_time) * 1000  # ms
            throughput = batch_size / (total_time / 1000)  # ops/s
            
            self.results.add_metric(f"bulk_insert_async_{batch_size}_latency", total_time, "ms")
            self.results.add_metric(f"bulk_insert_async_{batch_size}_throughput", throughput, "ops/s")
            
            print(f"    ✅ {batch_size} registros: {total_time:.2f}ms ({throughput:.0f} ops/s)")
    
    def benchmark_query(self, iterations: int = 1000):
        """Benchmark de consultas."""
        print(f"📊 Executando benchmark de consultas ({iterations} iterações)...")
        
        # Primeiro, inserir alguns dados para consultar
        test_users = []
        for i in range(100):
            user = BenchmarkModel(
                id=uuid.uuid4(),
                name=f"QueryUser {i}",
                email=f"query{i}@example.com",
                age=20 + (i % 50),
                tags=[f"query{i}", f"category{i%10}"],
                scores={i, i+1, i+2}
            )
            test_users.append(user)
        
        BenchmarkModel.bulk_create(test_users)
        
        # Benchmark de consultas
        times = []
        
        for i in range(iterations):
            start_time = time.time()
            
            # Consulta por email (campo indexado)
            user = BenchmarkModel.get(email=f"query{i%100}@example.com")
            
            end_time = time.time()
            times.append((end_time - start_time) * 1000)
        
        # Calcular métricas
        self.results.add_batch_metric("query_latency", times, "ms")
        self.results.add_metric("query_throughput", iterations / (sum(times) / 1000), "ops/s")
        
        print(f"✅ Consulta: {statistics.mean(times):.2f}ms (média)")
    
    async def benchmark_query_async(self, iterations: int = 1000):
        """Benchmark de consultas (assíncrono)."""
        print(f"📊 Executando benchmark de consultas assíncronas ({iterations} iterações)...")
        
        # Primeiro, inserir alguns dados para consultar
        test_users = []
        for i in range(100):
            user = BenchmarkModel(
                id=uuid.uuid4(),
                name=f"AsyncQueryUser {i}",
                email=f"asyncquery{i}@example.com",
                age=20 + (i % 50),
                tags=[f"asyncquery{i}", f"category{i%10}"],
                scores={i, i+1, i+2}
            )
            test_users.append(user)
        
        await BenchmarkModel.bulk_create_async(test_users)
        
        # Benchmark de consultas
        times = []
        
        for i in range(iterations):
            start_time = time.time()
            
            # Consulta por email (campo indexado)
            user = await BenchmarkModel.get_async(email=f"asyncquery{i%100}@example.com")
            
            end_time = time.time()
            times.append((end_time - start_time) * 1000)
        
        # Calcular métricas
        self.results.add_batch_metric("query_async_latency", times, "ms")
        self.results.add_metric("query_async_throughput", iterations / (sum(times) / 1000), "ops/s")
        
        print(f"✅ Consulta assíncrona: {statistics.mean(times):.2f}ms (média)")
    
    def benchmark_update(self, iterations: int = 500):
        """Benchmark de atualizações."""
        print(f"📊 Executando benchmark de atualizações ({iterations} iterações)...")
        
        # Primeiro, inserir dados para atualizar
        test_users = []
        for i in range(iterations):
            user = BenchmarkModel(
                id=uuid.uuid4(),
                name=f"UpdateUser {i}",
                email=f"update{i}@example.com",
                age=20 + (i % 50),
                tags=[f"update{i}"],
                scores={i}
            )
            test_users.append(user)
        
        BenchmarkModel.bulk_create(test_users)
        
        # Benchmark de atualizações
        times = []
        
        for i, user in enumerate(test_users):
            start_time = time.time()
            
            user.update(age=user.age + 1, tags=user.tags + [f"updated{i}"])
            
            end_time = time.time()
            times.append((end_time - start_time) * 1000)
        
        # Calcular métricas
        self.results.add_batch_metric("update_latency", times, "ms")
        self.results.add_metric("update_throughput", iterations / (sum(times) / 1000), "ops/s")
        
        print(f"✅ Atualização: {statistics.mean(times):.2f}ms (média)")
    
    async def benchmark_update_async(self, iterations: int = 500):
        """Benchmark de atualizações (assíncrono)."""
        print(f"📊 Executando benchmark de atualizações assíncronas ({iterations} iterações)...")
        
        # Primeiro, inserir dados para atualizar
        test_users = []
        for i in range(iterations):
            user = BenchmarkModel(
                id=uuid.uuid4(),
                name=f"AsyncUpdateUser {i}",
                email=f"asyncupdate{i}@example.com",
                age=20 + (i % 50),
                tags=[f"asyncupdate{i}"],
                scores={i}
            )
            test_users.append(user)
        
        await BenchmarkModel.bulk_create_async(test_users)
        
        # Benchmark de atualizações
        times = []
        
        for i, user in enumerate(test_users):
            start_time = time.time()
            
            await user.update_async(age=user.age + 1, tags=user.tags + [f"asyncupdated{i}"])
            
            end_time = time.time()
            times.append((end_time - start_time) * 1000)
        
        # Calcular métricas
        self.results.add_batch_metric("update_async_latency", times, "ms")
        self.results.add_metric("update_async_throughput", iterations / (sum(times) / 1000), "ops/s")
        
        print(f"✅ Atualização assíncrona: {statistics.mean(times):.2f}ms (média)")
    
    def run_sync_benchmarks(self):
        """Executa todos os benchmarks síncronos."""
        print("🚀 Iniciando benchmarks síncronos...")
        
        self.benchmark_single_insert(1000)
        self.benchmark_bulk_insert([10, 100, 1000])
        self.benchmark_query(1000)
        self.benchmark_update(500)
        
        print("✅ Benchmarks síncronos concluídos!")
    
    async def run_async_benchmarks(self):
        """Executa todos os benchmarks assíncronos."""
        print("🚀 Iniciando benchmarks assíncronos...")
        
        await self.benchmark_single_insert_async(1000)
        await self.benchmark_bulk_insert_async([10, 100, 1000])
        await self.benchmark_query_async(1000)
        await self.benchmark_update_async(500)
        
        print("✅ Benchmarks assíncronos concluídos!")
    
    def cleanup(self):
        """Limpa os dados de teste."""
        print("🧹 Limpando dados de teste...")
        
        # Deletar todos os registros de teste
        all_users = BenchmarkModel.all().all()
        for user in all_users:
            user.delete()
        
        print("✅ Limpeza concluída!")

def main():
    """Função principal do benchmark."""
    parser = argparse.ArgumentParser(description="Benchmark automatizado para CaspyORM")
    parser.add_argument("--contact-points", nargs="+", default=["localhost"], 
                       help="Pontos de contato do Cassandra")
    parser.add_argument("--keyspace", default="benchmark_keyspace",
                       help="Keyspace para os testes")
    parser.add_argument("--output", default="benchmark_results.json",
                       help="Arquivo de saída JSON")
    parser.add_argument("--sync-only", action="store_true",
                       help="Executar apenas benchmarks síncronos")
    parser.add_argument("--async-only", action="store_true",
                       help="Executar apenas benchmarks assíncronos")
    
    args = parser.parse_args()
    
    # Criar runner
    runner = BenchmarkRunner(args.contact_points, args.keyspace)
    
    try:
        if not args.async_only:
            print("🔄 Executando benchmarks síncronos...")
            runner.setup()
            runner.run_sync_benchmarks()
            runner.cleanup()
        
        if not args.sync_only:
            print("🔄 Executando benchmarks assíncronos...")
            asyncio.run(runner.setup_async())
            asyncio.run(runner.run_async_benchmarks())
            runner.cleanup()
        
        # Salvar resultados
        runner.results.save_to_file(args.output)
        runner.results.print_summary()
        
        print(f"\n📄 Resultados salvos em: {args.output}")
        
    except Exception as e:
        print(f"❌ Erro durante o benchmark: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 