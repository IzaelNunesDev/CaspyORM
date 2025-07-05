# caspyorm/results.py

from typing import Type

def _map_row_to_instance(model_cls, row_dict):
    # Importação local para evitar importação circular
    from .model import Model
    """Mapeia um dicionário (linha do DB) para uma instância do modelo."""
    # Aqui estamos assumindo que os nomes das colunas correspondem aos nomes dos campos.
    # A metaclasse `__init__` do nosso modelo espera kwargs.
    return model_cls(**row_dict)