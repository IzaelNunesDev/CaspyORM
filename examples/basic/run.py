#!/usr/bin/env python3
"""
Script para executar a aplicação de demonstração.
"""
import sys
import os

# Adicionar o diretório pai ao path para importar a biblioteca
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Iniciando CaspyORM Demo API...")
    print("📖 Documentação disponível em: http://localhost:8000/docs")
    print("🔍 ReDoc disponível em: http://localhost:8000/redoc")
    print("🏥 Health check em: http://localhost:8000/health")
    print("📊 Setup demo em: http://localhost:8000/demo/setup")
    print()
    
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    ) 