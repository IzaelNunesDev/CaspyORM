#!/usr/bin/env python3
"""
Script para executar benchmarks de forma automatizada.
Pode ser usado em CI/CD para detectar regressões de performance.
"""

import os
import sys
import subprocess
import json
import argparse
from datetime import datetime
from pathlib import Path

def run_benchmark(contact_points=None, keyspace=None, output_file=None):
    """Executa o benchmark completo."""
    cmd = [
        sys.executable, 
        "scripts/benchmark/full_benchmark.py"
    ]
    
    if contact_points:
        cmd.extend(["--contact-points"] + contact_points)
    
    if keyspace:
        cmd.extend(["--keyspace", keyspace])
    
    if output_file:
        cmd.extend(["--output", output_file])
    
    print(f"🚀 Executando: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Benchmark executado com sucesso!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar benchmark: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def compare_with_baseline(current_file, baseline_file, threshold=0.1):
    """Compara resultados atuais com baseline."""
    cmd = [
        sys.executable,
        "scripts/benchmark/compare_results.py",
        baseline_file,
        current_file,
        "--threshold", str(threshold)
    ]
    
    print(f"🔍 Comparando: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Comparação executada com sucesso!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Regressões detectadas: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def create_baseline_if_not_exists(baseline_file):
    """Cria baseline se não existir."""
    if not os.path.exists(baseline_file):
        print(f"📊 Criando baseline: {baseline_file}")
        return run_benchmark(output_file=baseline_file)
    else:
        print(f"📊 Baseline já existe: {baseline_file}")
        return True

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Executar benchmarks automatizados")
    parser.add_argument("--contact-points", nargs="+", default=["localhost"],
                       help="Pontos de contato do Cassandra")
    parser.add_argument("--keyspace", default="benchmark_keyspace",
                       help="Keyspace para os testes")
    parser.add_argument("--baseline", default="benchmark_baseline.json",
                       help="Arquivo de baseline")
    parser.add_argument("--output", default="benchmark_current.json",
                       help="Arquivo de saída para resultados atuais")
    parser.add_argument("--threshold", type=float, default=0.1,
                       help="Threshold para detectar regressões (padrão: 0.1 = 10%)")
    parser.add_argument("--create-baseline", action="store_true",
                       help="Criar novo baseline")
    parser.add_argument("--skip-comparison", action="store_true",
                       help="Pular comparação com baseline")
    
    args = parser.parse_args()
    
    # Verificar se estamos no diretório correto
    if not os.path.exists("scripts/benchmark/full_benchmark.py"):
        print("❌ Execute este script do diretório raiz do projeto")
        sys.exit(1)
    
    print("🚀 Iniciando execução de benchmarks automatizados")
    print(f"   Contact Points: {args.contact_points}")
    print(f"   Keyspace: {args.keyspace}")
    print(f"   Baseline: {args.baseline}")
    print(f"   Output: {args.output}")
    print(f"   Threshold: {args.threshold}")
    print()
    
    # Criar baseline se necessário
    if args.create_baseline or not os.path.exists(args.baseline):
        if not create_baseline_if_not_exists(args.baseline):
            print("❌ Falha ao criar baseline")
            sys.exit(1)
    
    # Executar benchmark atual
    print("🔄 Executando benchmark atual...")
    if not run_benchmark(
        contact_points=args.contact_points,
        keyspace=args.keyspace,
        output_file=args.output
    ):
        print("❌ Falha ao executar benchmark")
        sys.exit(1)
    
    # Comparar com baseline
    if not args.skip_comparison and os.path.exists(args.baseline):
        print("🔄 Comparando com baseline...")
        success = compare_with_baseline(
            current_file=args.output,
            baseline_file=args.baseline,
            threshold=args.threshold
        )
        
        if not success:
            print("❌ Regressões de performance detectadas!")
            sys.exit(1)
        else:
            print("✅ Nenhuma regressão detectada!")
    else:
        print("⏭️  Comparação com baseline pulada")
    
    print("🎉 Benchmarks concluídos com sucesso!")

if __name__ == "__main__":
    main() 