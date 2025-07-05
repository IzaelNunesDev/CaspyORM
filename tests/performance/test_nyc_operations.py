#!/usr/bin/env python3
"""
Teste Completo das Operações da CaspyORM com Dados Reais NYC TLC
Testa: autoschema, consultas, métricas de performance, validação de dados
"""

import time
import psutil
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import statistics

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from caspyorm import Model, fields, connection
from caspyorm.exceptions import CaspyORMException
import pandas as pd
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NYCTaxiClean(Model):
    """Modelo para dados de táxi NYC TLC"""
    __table_name__ = "nyc_taxi_clean"
    
    # Campos do modelo
    trip_id = fields.UUID(primary_key=True)
    vendor_id = fields.Text(partition_key=True)
    pickup_datetime = fields.Timestamp(clustering_key=True)
    dropoff_datetime = fields.Timestamp()
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

class PerformanceMetrics:
    """Classe para coletar métricas de performance"""
    
    def __init__(self):
        self.operations = []
        self.memory_usage = []
        self.start_time = None
        
    def start_operation(self, operation_name: str):
        """Inicia uma operação"""
        self.start_time = time.time()
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            'operation': operation_name,
            'start_time': self.start_time,
            'memory_before': memory_before
        }
    
    def end_operation(self, operation_data: Dict, result_count: int = None):
        """Finaliza uma operação e coleta métricas"""
        end_time = time.time()
        process = psutil.Process()
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        
        duration = end_time - operation_data['start_time']
        memory_delta = memory_after - operation_data['memory_before']
        
        operation_result = {
            'operation': operation_data['operation'],
            'duration': duration,
            'memory_before': operation_data['memory_before'],
            'memory_after': memory_after,
            'memory_delta': memory_delta,
            'result_count': result_count,
            'operations_per_second': result_count / duration if result_count and duration > 0 else 0
        }
        
        self.operations.append(operation_result)
        self.memory_usage.append(memory_after)
        
        return operation_result
    
    def print_summary(self):
        """Imprime resumo das métricas"""
        print("\n" + "="*80)
        print("📊 RESUMO DE PERFORMANCE")
        print("="*80)
        
        for op in self.operations:
            print(f"\n🔍 {op['operation']}")
            print(f"   ⏱️  Duração: {op['duration']:.3f}s")
            print(f"   💾 Memória: {op['memory_before']:.1f}MB → {op['memory_after']:.1f}MB (Δ{op['memory_delta']:+.1f}MB)")
            if op['result_count']:
                print(f"   📈 Resultados: {op['result_count']:,}")
                print(f"   🚀 Ops/segundo: {op['operations_per_second']:.1f}")
        
        # Estatísticas gerais
        if self.operations:
            durations = [op['duration'] for op in self.operations]
            memory_peaks = [op['memory_after'] for op in self.operations]
            
            print(f"\n📊 ESTATÍSTICAS GERAIS:")
            print(f"   ⏱️  Tempo total: {sum(durations):.3f}s")
            print(f"   💾 Pico de memória: {max(memory_peaks):.1f}MB")
            print(f"   📈 Operação mais rápida: {min(durations):.3f}s")
            print(f"   🐌 Operação mais lenta: {max(durations):.3f}s")
            print(f"   📊 Tempo médio: {statistics.mean(durations):.3f}s")

def test_autoschema():
    """Testa a funcionalidade de autoschema"""
    print("\n🔧 Testando AutoSchema...")
    
    try:
        # Testar sincronização do schema
        start_time = time.time()
        NYCTaxiClean.sync_table(auto_apply=True)
        sync_time = time.time() - start_time
        
        print(f"   ✅ Schema sincronizado em {sync_time:.3f}s")
        
        # Verificar se a tabela existe
        session = connection.get_session()
        if session and session.cluster and session.cluster.metadata:
            keyspace = session.cluster.metadata.keyspaces.get('nyc_taxi_clean')
            if keyspace and 'nyc_taxi_clean' in keyspace.tables:
                table = keyspace.tables['nyc_taxi_clean']
                print(f"   📋 Tabela encontrada com {len(table.columns)} colunas")
                return True
            else:
                print("   ❌ Tabela não encontrada")
                return False
        else:
            print("   ❌ Sessão não disponível")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro no autoschema: {e}")
        return False

def test_count_operations(metrics: PerformanceMetrics):
    """Testa operações de contagem"""
    print("\n🔢 Testando Operações de Contagem...")
    
    # Contagem total
    op_data = metrics.start_operation("Contagem Total")
    try:
        all_records = list(NYCTaxiClean.all())
        total_count = len(all_records)
        result = metrics.end_operation(op_data, total_count)
        print(f"   📊 Total de registros: {total_count:,}")
        print(f"   ⏱️  Tempo: {result['duration']:.3f}s")
    except Exception as e:
        print(f"   ❌ Erro na contagem total: {e}")
    
    # Contagem por vendor_id
    op_data = metrics.start_operation("Contagem por Vendor")
    try:
        vendor_counts = {}
        for vendor in ['1', '2']:  # Vendors conhecidos
            vendor_records = list(NYCTaxiClean.filter(vendor_id=vendor))
            count = len(vendor_records)
            vendor_counts[vendor] = count
            print(f"   🚕 Vendor {vendor}: {count:,} registros")
        
        result = metrics.end_operation(op_data, sum(vendor_counts.values()))
        print(f"   ⏱️  Tempo: {result['duration']:.3f}s")
    except Exception as e:
        print(f"   ❌ Erro na contagem por vendor: {e}")

def test_query_operations(metrics: PerformanceMetrics):
    """Testa operações de consulta"""
    print("\n🔍 Testando Operações de Consulta...")
    
    # Consulta simples - primeiros 10 registros
    op_data = metrics.start_operation("Consulta Simples (10 registros)")
    try:
        all_records = list(NYCTaxiClean.all())
        records = all_records[:10]
        result = metrics.end_operation(op_data, len(records))
        print(f"   📋 Primeiros 10 registros: {len(records)} encontrados")
        if records:
            first_record = records[0]
            print(f"   🚕 Exemplo: Vendor {first_record.vendor_id}, ${first_record.total_amount:.2f}")
        print(f"   ⏱️  Tempo: {result['duration']:.3f}s")
    except Exception as e:
        print(f"   ❌ Erro na consulta simples: {e}")
    
    # Consulta com filtro
    op_data = metrics.start_operation("Consulta com Filtro (vendor_id=1)")
    try:
        filtered_records = list(NYCTaxiClean.filter(vendor_id='1'))
        result = metrics.end_operation(op_data, len(filtered_records))
        print(f"   🔍 Registros vendor_id=1: {len(filtered_records)} encontrados")
        if filtered_records:
            avg_fare = sum(r.fare_amount for r in filtered_records) / len(filtered_records)
            print(f"   💰 Tarifa média: ${avg_fare:.2f}")
        print(f"   ⏱️  Tempo: {result['duration']:.3f}s")
    except Exception as e:
        print(f"   ❌ Erro na consulta com filtro: {e}")
    
    # Consulta com ordenação
    op_data = metrics.start_operation("Consulta Ordenada (por total_amount)")
    try:
        all_records = list(NYCTaxiClean.all())
        ordered_records = sorted(all_records, key=lambda x: x.total_amount, reverse=True)[:5]
        result = metrics.end_operation(op_data, len(ordered_records))
        print(f"   🏆 Top 5 tarifas mais altas:")
        for i, record in enumerate(ordered_records, 1):
            print(f"      {i}. ${record.total_amount:.2f} (Vendor {record.vendor_id})")
        print(f"   ⏱️  Tempo: {result['duration']:.3f}s")
    except Exception as e:
        print(f"   ❌ Erro na consulta ordenada: {e}")

def test_aggregation_operations(metrics: PerformanceMetrics):
    """Testa operações de agregação"""
    print("\n📊 Testando Operações de Agregação...")
    
    # Estatísticas básicas
    op_data = metrics.start_operation("Estatísticas Básicas")
    try:
        all_records = list(NYCTaxiClean.all())
        result = metrics.end_operation(op_data, len(all_records))
        
        if all_records:
            fares = [r.fare_amount for r in all_records]
            distances = [r.trip_distance for r in all_records]
            passengers = [r.passenger_count for r in all_records]
            
            print(f"   📈 Estatísticas de Tarifa:")
            print(f"      Média: ${statistics.mean(fares):.2f}")
            print(f"      Mediana: ${statistics.median(fares):.2f}")
            print(f"      Min: ${min(fares):.2f}")
            print(f"      Max: ${max(fares):.2f}")
            
            print(f"   📏 Estatísticas de Distância:")
            print(f"      Média: {statistics.mean(distances):.2f} milhas")
            print(f"      Mediana: {statistics.median(distances):.2f} milhas")
            
            print(f"   👥 Estatísticas de Passageiros:")
            print(f"      Média: {statistics.mean(passengers):.1f}")
            print(f"      Moda: {max(set(passengers), key=passengers.count)}")
        
        print(f"   ⏱️  Tempo: {result['duration']:.3f}s")
    except Exception as e:
        print(f"   ❌ Erro nas estatísticas: {e}")

def test_data_validation(metrics: PerformanceMetrics):
    """Testa validação e qualidade dos dados"""
    print("\n✅ Testando Validação de Dados...")
    
    op_data = metrics.start_operation("Validação de Dados")
    try:
        all_records = list(NYCTaxiClean.objects.all())
        result = metrics.end_operation(op_data, len(all_records))
        
        if all_records:
            # Verificar integridade dos dados
            valid_records = 0
            invalid_records = 0
            issues = []
            
            for record in all_records:
                is_valid = True
                
                # Verificar campos obrigatórios
                if not record.vendor_id or not record.pickup_datetime:
                    is_valid = False
                    issues.append("vendor_id ou pickup_datetime vazios")
                
                # Verificar valores lógicos
                if record.fare_amount < 0:
                    is_valid = False
                    issues.append("tarifa negativa")
                
                if record.trip_distance < 0:
                    is_valid = False
                    issues.append("distância negativa")
                
                if record.passenger_count < 0 or record.passenger_count > 10:
                    is_valid = False
                    issues.append("número de passageiros inválido")
                
                if is_valid:
                    valid_records += 1
                else:
                    invalid_records += 1
            
            print(f"   ✅ Registros válidos: {valid_records:,} ({valid_records/len(all_records)*100:.1f}%)")
            print(f"   ❌ Registros inválidos: {invalid_records:,} ({invalid_records/len(all_records)*100:.1f}%)")
            
            if issues:
                issue_counts = {}
                for issue in issues:
                    issue_counts[issue] = issue_counts.get(issue, 0) + 1
                print(f"   🔍 Principais problemas encontrados:")
                for issue, count in issue_counts.items():
                    print(f"      - {issue}: {count} ocorrências")
        
        print(f"   ⏱️  Tempo: {result['duration']:.3f}s")
    except Exception as e:
        print(f"   ❌ Erro na validação: {e}")

def test_complex_queries(metrics: PerformanceMetrics):
    """Testa consultas mais complexas"""
    print("\n🧮 Testando Consultas Complexas...")
    
    # Consulta com múltiplos filtros
    op_data = metrics.start_operation("Consulta Múltiplos Filtros")
    try:
        # Corridas com tarifa alta e múltiplos passageiros
        complex_records = list(
            NYCTaxiClean.objects.filter(
                vendor_id='1',
                passenger_count__gte=3,
                fare_amount__gte=50.0
            ).limit(10)
        )
        result = metrics.end_operation(op_data, len(complex_records))
        print(f"   🔍 Corridas caras com 3+ passageiros: {len(complex_records)} encontradas")
        if complex_records:
            avg_fare = sum(r.fare_amount for r in complex_records) / len(complex_records)
            print(f"   💰 Tarifa média: ${avg_fare:.2f}")
        print(f"   ⏱️  Tempo: {result['duration']:.3f}s")
    except Exception as e:
        print(f"   ❌ Erro na consulta complexa: {e}")
    
    # Consulta por período
    op_data = metrics.start_operation("Consulta por Período")
    try:
        # Encontrar um período de dados para testar
        sample_record = NYCTaxiClean.objects.first()
        if sample_record:
            start_date = sample_record.pickup_datetime
            end_date = start_date + timedelta(hours=1)
            
            period_records = list(
                NYCTaxiClean.objects.filter(
                    pickup_datetime__gte=start_date,
                    pickup_datetime__lt=end_date
                ).limit(50)
            )
            result = metrics.end_operation(op_data, len(period_records))
            print(f"   📅 Corridas em 1 hora: {len(period_records)} encontradas")
            print(f"   ⏱️  Tempo: {result['duration']:.3f}s")
    except Exception as e:
        print(f"   ❌ Erro na consulta por período: {e}")

def main():
    """Função principal"""
    print("🚀 TESTE COMPLETO DAS OPERAÇÕES CASPYORM COM DADOS REAIS NYC TLC")
    print("="*80)
    
    # Inicializar métricas
    metrics = PerformanceMetrics()
    
    try:
        # Conectar ao Cassandra
        print("\n🔌 Conectando ao Cassandra...")
        connection.connect(contact_points=['localhost'], port=9042, keyspace='nyc_taxi_clean')
        print("   ✅ Conectado com sucesso!")
        
        # Testar autoschema
        if not test_autoschema():
            print("❌ Falha no autoschema. Abortando testes.")
            return
        
        # Executar todos os testes
        test_count_operations(metrics)
        test_query_operations(metrics)
        test_aggregation_operations(metrics)
        test_data_validation(metrics)
        test_complex_queries(metrics)
        
        # Imprimir resumo final
        metrics.print_summary()
        
        print("\n🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Fechar conexão
        try:
            connection.disconnect()
            print("\n🔌 Conexão fechada.")
        except:
            pass

if __name__ == "__main__":
    main() 