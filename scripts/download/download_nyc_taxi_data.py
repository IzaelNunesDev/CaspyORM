#!/usr/bin/env python3
"""
Script para baixar e processar dados reais de táxi de Nova York
Baseado na API TLC: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
"""

import requests
import pandas as pd
import os
import time
from datetime import datetime
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NYCTaxiDataDownloader:
    """Classe para baixar dados de táxi de Nova York"""
    
    def __init__(self, data_dir="nyc_taxi_data"):
        self.data_dir = data_dir
        self.base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data"
        
        # Cria diretório se não existir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def get_available_datasets(self):
        """Retorna lista de datasets disponíveis"""
        datasets = {
            "yellow": {
                "name": "Yellow Taxi Trip Records",
                "url_pattern": "yellow_tripdata_{year}-{month:02d}.parquet"
            },
            "green": {
                "name": "Green Taxi Trip Records", 
                "url_pattern": "green_tripdata_{year}-{month:02d}.parquet"
            },
            "fhv": {
                "name": "For-Hire Vehicle Trip Records",
                "url_pattern": "fhv_tripdata_{year}-{month:02d}.parquet"
            },
            "fhvhv": {
                "name": "High Volume For-Hire Vehicle Trip Records",
                "url_pattern": "fhvhv_tripdata_{year}-{month:02d}.parquet"
            }
        }
        return datasets
    
    def download_file(self, url, filename):
        """Baixa um arquivo específico"""
        try:
            logger.info(f"Baixando: {filename}")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            filepath = os.path.join(self.data_dir, filename)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Download concluído: {filename}")
            return filepath
            
        except Exception as e:
            logger.error(f"Erro ao baixar {filename}: {e}")
            return None
    
    def download_monthly_data(self, year, month, dataset_type="yellow"):
        """Baixa dados mensais de um tipo específico"""
        datasets = self.get_available_datasets()
        
        if dataset_type not in datasets:
            logger.error(f"Tipo de dataset inválido: {dataset_type}")
            return None
        
        url_pattern = datasets[dataset_type]["url_pattern"]
        filename = url_pattern.format(year=year, month=month)
        url = f"{self.base_url}/{filename}"
        
        return self.download_file(url, filename)
    
    def download_recent_data(self, months_back=3, dataset_type="yellow"):
        """Baixa dados dos últimos meses"""
        current_date = datetime.now()
        downloaded_files = []
        
        for i in range(months_back):
            target_date = current_date.replace(day=1) - pd.DateOffset(months=i)
            year = target_date.year
            month = target_date.month
            
            logger.info(f"Baixando dados de {year}-{month:02d}")
            filepath = self.download_monthly_data(year, month, dataset_type)
            
            if filepath:
                downloaded_files.append(filepath)
            
            # Pausa entre downloads para não sobrecarregar o servidor
            time.sleep(1)
        
        return downloaded_files
    
    def process_parquet_file(self, filepath, sample_size=None):
        """Processa um arquivo Parquet e retorna DataFrame"""
        try:
            logger.info(f"Processando: {filepath}")
            
            if sample_size:
                # Lê apenas uma amostra para testes
                df = pd.read_parquet(filepath, nrows=sample_size)
                logger.info(f"Amostra carregada: {len(df)} registros")
            else:
                # Lê arquivo completo
                df = pd.read_parquet(filepath)
                logger.info(f"Arquivo carregado: {len(df)} registros")
            
            return df
            
        except Exception as e:
            logger.error(f"Erro ao processar {filepath}: {e}")
            return None
    
    def convert_to_caspyorm_format(self, df, dataset_type="yellow"):
        """Converte DataFrame para formato compatível com CaspyORM"""
        try:
            # Mapeia colunas do TLC para nosso modelo
            column_mapping = {
                'VendorID': 'vendor_id',
                'tpep_pickup_datetime': 'pickup_datetime',
                'tpep_dropoff_datetime': 'dropoff_datetime',
                'passenger_count': 'passenger_count',
                'trip_distance': 'trip_distance',
                'pickup_longitude': 'pickup_longitude',
                'pickup_latitude': 'pickup_latitude',
                'dropoff_longitude': 'dropoff_longitude',
                'dropoff_latitude': 'dropoff_latitude',
                'RatecodeID': 'rate_code_id',
                'store_and_fwd_flag': 'store_and_fwd_flag',
                'payment_type': 'payment_type',
                'fare_amount': 'fare_amount',
                'extra': 'extra',
                'mta_tax': 'mta_tax',
                'tip_amount': 'tip_amount',
                'tolls_amount': 'tolls_amount',
                'improvement_surcharge': 'improvement_surcharge',
                'total_amount': 'total_amount',
                'congestion_surcharge': 'congestion_surcharge'
            }
            
            # Renomeia colunas
            df_renamed = df.rename(columns=column_mapping)
            
            # Adiciona campos que não existem no TLC mas precisamos
            df_renamed['trip_id'] = None  # Será gerado pelo CaspyORM
            df_renamed['pickup_location'] = 'Unknown'
            df_renamed['dropoff_location'] = 'Unknown'
            df_renamed['trip_tags'] = []
            df_renamed['trip_features'] = set()
            df_renamed['trip_metadata'] = {}
            df_renamed['created_at'] = datetime.utcnow()
            df_renamed['updated_at'] = datetime.utcnow()
            
            # Remove registros com dados inválidos
            df_renamed = df_renamed.dropna(subset=['pickup_datetime', 'dropoff_datetime'])
            
            logger.info(f"Conversão concluída: {len(df_renamed)} registros válidos")
            return df_renamed
            
        except Exception as e:
            logger.error(f"Erro na conversão: {e}")
            return None
    
    def create_sample_dataset(self, sample_size=10000):
        """Cria um dataset de amostra para testes"""
        logger.info("Criando dataset de amostra para testes...")
        
        # Baixa dados recentes
        files = self.download_recent_data(months_back=1, dataset_type="yellow")
        
        if not files:
            logger.error("Nenhum arquivo foi baixado")
            return None
        
        # Processa primeiro arquivo
        df = self.process_parquet_file(files[0], sample_size=sample_size)
        
        if df is None:
            logger.error("Falha ao processar arquivo")
            return None
        
        # Converte para formato CaspyORM
        df_converted = self.convert_to_caspyorm_format(df)
        
        if df_converted is None:
            logger.error("Falha na conversão")
            return None
        
        # Salva como CSV para uso posterior
        output_file = os.path.join(self.data_dir, "sample_taxi_data.csv")
        df_converted.to_csv(output_file, index=False)
        
        logger.info(f"Dataset de amostra salvo: {output_file}")
        return output_file

def main():
    """Função principal"""
    downloader = NYCTaxiDataDownloader()
    
    print("🚕 DOWNLOADER DE DADOS DE TÁXI NYC 🚕")
    print("=" * 50)
    
    # Cria dataset de amostra
    sample_file = downloader.create_sample_dataset(sample_size=10000)
    
    if sample_file:
        print(f"✅ Dataset de amostra criado: {sample_file}")
        print(f"📊 Tamanho: {os.path.getsize(sample_file) / 1024 / 1024:.2f} MB")
    else:
        print("❌ Falha ao criar dataset de amostra")

if __name__ == "__main__":
    main() 