#!/usr/bin/env python3
"""
Script para comparar resultados de benchmark e detectar regressões de performance.
"""

import json
import argparse
import sys
from typing import Dict, Any, List
from datetime import datetime

def load_results(filename: str) -> Dict[str, Any]:
    """Carrega resultados de benchmark de um arquivo JSON."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {filename}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ Erro ao decodificar JSON: {filename}")
        sys.exit(1)

def compare_metrics(baseline: Dict[str, Any], current: Dict[str, Any], threshold: float = 0.1) -> Dict[str, Any]:
    """Compara métricas entre baseline e current."""
    comparison = {
        "timestamp": datetime.now().isoformat(),
        "baseline_file": baseline.get("timestamp", "unknown"),
        "current_file": current.get("timestamp", "unknown"),
        "regressions": [],
        "improvements": [],
        "unchanged": [],
        "summary": {
            "total_metrics": 0,
            "regressions": 0,
            "improvements": 0,
            "unchanged": 0
        }
    }
    
    baseline_metrics = baseline.get("metrics", {})
    current_metrics = current.get("metrics", {})
    
    # Comparar métricas que existem em ambos
    all_metrics = set(baseline_metrics.keys()) | set(current_metrics.keys())
    
    for metric_name in all_metrics:
        baseline_data = baseline_metrics.get(metric_name)
        current_data = current_metrics.get(metric_name)
        
        if not baseline_data or not current_data:
            continue
        
        # Extrair valores para comparação
        baseline_value = extract_metric_value(baseline_data)
        current_value = extract_metric_value(current_data)
        
        if baseline_value is None or current_value is None:
            continue
        
        comparison["summary"]["total_metrics"] += 1
        
        # Calcular diferença percentual
        if baseline_value != 0:
            change_percent = ((current_value - baseline_value) / baseline_value) * 100
        else:
            change_percent = 0
        
        metric_info = {
            "metric": metric_name,
            "baseline": baseline_value,
            "current": current_value,
            "change_percent": change_percent,
            "unit": extract_unit(baseline_data)
        }
        
        # Classificar mudança
        if change_percent > threshold * 100:  # Piorou (aumentou)
            comparison["regressions"].append(metric_info)
            comparison["summary"]["regressions"] += 1
        elif change_percent < -threshold * 100:  # Melhorou (diminuiu)
            comparison["improvements"].append(metric_info)
            comparison["summary"]["improvements"] += 1
        else:
            comparison["unchanged"].append(metric_info)
            comparison["summary"]["unchanged"] += 1
    
    return comparison

def extract_metric_value(metric_data: Any) -> float:
    """Extrai o valor principal de uma métrica."""
    if isinstance(metric_data, list):
        # Métrica simples - pegar o último valor
        if metric_data:
            return metric_data[-1].get("value", 0)
        return 0
    elif isinstance(metric_data, dict):
        # Métrica com estatísticas - usar a média
        return metric_data.get("mean", 0)
    return 0

def extract_unit(metric_data: Any) -> str:
    """Extrai a unidade de uma métrica."""
    if isinstance(metric_data, list):
        if metric_data:
            return metric_data[-1].get("unit", "unknown")
        return "unknown"
    elif isinstance(metric_data, dict):
        return metric_data.get("unit", "unknown")
    return "unknown"

def print_comparison(comparison: Dict[str, Any]):
    """Imprime a comparação de forma legível."""
    print("\n" + "="*80)
    print("COMPARAÇÃO DE BENCHMARK")
    print("="*80)
    print(f"Baseline: {comparison['baseline_file']}")
    print(f"Current:  {comparison['current_file']}")
    print(f"Timestamp: {comparison['timestamp']}")
    print()
    
    summary = comparison["summary"]
    print(f"📊 RESUMO:")
    print(f"   Total de métricas: {summary['total_metrics']}")
    print(f"   Regressões: {summary['regressions']}")
    print(f"   Melhorias: {summary['improvements']}")
    print(f"   Inalteradas: {summary['unchanged']}")
    print()
    
    if comparison["regressions"]:
        print("❌ REGRESSÕES DETECTADAS:")
        print("-" * 50)
        for reg in comparison["regressions"]:
            print(f"  {reg['metric']}:")
            print(f"    {reg['baseline']:.2f} → {reg['current']:.2f} {reg['unit']}")
            print(f"    Mudança: +{reg['change_percent']:.1f}%")
            print()
    
    if comparison["improvements"]:
        print("✅ MELHORIAS DETECTADAS:")
        print("-" * 50)
        for imp in comparison["improvements"]:
            print(f"  {imp['metric']}:")
            print(f"    {imp['baseline']:.2f} → {imp['current']:.2f} {imp['unit']}")
            print(f"    Mudança: {imp['change_percent']:.1f}%")
            print()
    
    if comparison["unchanged"]:
        print("➡️  MÉTRICAS INALTERADAS:")
        print("-" * 50)
        for unchanged in comparison["unchanged"][:10]:  # Mostrar apenas as primeiras 10
            print(f"  {unchanged['metric']}: {unchanged['change_percent']:.1f}%")
        
        if len(comparison["unchanged"]) > 10:
            print(f"  ... e mais {len(comparison['unchanged']) - 10} métricas")
        print()

def save_comparison(comparison: Dict[str, Any], filename: str):
    """Salva a comparação em arquivo JSON."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)
    print(f"📄 Comparação salva em: {filename}")

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Comparar resultados de benchmark")
    parser.add_argument("baseline", help="Arquivo JSON com resultados baseline")
    parser.add_argument("current", help="Arquivo JSON com resultados atuais")
    parser.add_argument("--output", "-o", default="comparison_results.json",
                       help="Arquivo de saída para comparação")
    parser.add_argument("--threshold", "-t", type=float, default=0.1,
                       help="Threshold para detectar mudanças (padrão: 0.1 = 10%)")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Modo silencioso (apenas salvar arquivo)")
    
    args = parser.parse_args()
    
    # Carregar resultados
    print("📂 Carregando resultados...")
    baseline = load_results(args.baseline)
    current = load_results(args.current)
    
    # Comparar
    print("🔍 Comparando métricas...")
    comparison = compare_metrics(baseline, current, args.threshold)
    
    # Salvar comparação
    save_comparison(comparison, args.output)
    
    # Imprimir resumo
    if not args.quiet:
        print_comparison(comparison)
    
    # Retornar código de saída baseado em regressões
    if comparison["summary"]["regressions"] > 0:
        print(f"⚠️  {comparison['summary']['regressions']} regressões detectadas!")
        sys.exit(1)
    else:
        print("✅ Nenhuma regressão detectada!")
        sys.exit(0)

if __name__ == "__main__":
    main() 