# caspyorm/_internal/serialization.py
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Type, Optional

# Lidar com a importação opcional do Pydantic
try:
    from pydantic import BaseModel, create_model, Field
    PYDANTIC_V2 = True
    # O Pydantic V2 usa ConfigDict, enquanto o V1 usava uma classe Config.
    # Vamos focar na V2 por ser mais moderna.
except ImportError:
    PYDANTIC_V2 = False
    # Definir stubs para evitar erros se pydantic não estiver instalado
    class BaseModel: pass
    def create_model(*args, **kwargs): pass
    def Field(*args, **kwargs): pass

class CaspyJSONEncoder(json.JSONEncoder):
    """Encoder JSON customizado para tipos da CaspyORM."""
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        # Adicione outros tipos aqui se necessário
        return super().default(obj)

def model_to_dict(instance: "Model", by_alias: bool = False) -> Dict[str, Any]:
    """Serializa uma instância de modelo para um dicionário."""
    # `by_alias` será usado no futuro
    data = {}
    for key in instance.model_fields.keys():
        data[key] = getattr(instance, key, None)
    return data

def model_to_json(instance: "Model", by_alias: bool = False, indent: Optional[int] = None) -> str:
    """Serializa uma instância de modelo para uma string JSON."""
    return json.dumps(
        instance.model_dump(by_alias=by_alias), 
        cls=CaspyJSONEncoder, 
        indent=indent
    )

def generate_pydantic_model(
    model_cls: Type["Model"], 
    name: Optional[str] = None, 
    exclude: Optional[List[str]] = None
) -> Type[BaseModel]:
    """
    Gera dinamicamente um modelo Pydantic a partir de um modelo CaspyORM.
    """
    if not PYDANTIC_V2:
        raise ImportError("A funcionalidade de integração com Pydantic requer que o pacote 'pydantic' seja instalado.")

    exclude = exclude or []
    
    # Mapeia nossos tipos de campo para tipos Python/Pydantic
    type_mapping = {
        'uuid': uuid.UUID,
        'text': str,
        'int': int,
        'float': float,
        'boolean': bool,
        'timestamp': datetime,
        'varchar': str,  # Adicionado para compatibilidade
    }

    pydantic_fields: Dict[str, Any] = {}
    caspy_schema = model_cls.__caspy_schema__

    for field_name, field_details in caspy_schema['fields'].items():
        if field_name in exclude:
            continue
        
        # Obtém o tipo Python correspondente
        python_type = type_mapping.get(field_details['type'])
        if python_type is None:
            # Pula campos com tipos não mapeados por enquanto
            print(f"Aviso: tipo CQL '{field_details['type']}' não mapeado para Pydantic. Pulando campo '{field_name}'.")
            continue

        # Define se o campo é obrigatório ou opcional no Pydantic
        # Se for obrigatório na CaspyORM OU não tiver default, é obrigatório no Pydantic
        if field_details.get('required', False) or field_details.get('default') is None:
             pydantic_fields[field_name] = (python_type, ...) # '...' indica obrigatório
        else:
             # Caso contrário, é opcional com um valor padrão
             pydantic_fields[field_name] = (python_type, field_details['default'])

    # Gera o nome do modelo Pydantic se não for fornecido
    model_name = name or f"{model_cls.__name__}Pydantic"
    
    # Usa a função `create_model` do Pydantic para criar a classe dinamicamente
    pydantic_model = create_model(model_name, **pydantic_fields)
    
    return pydantic_model 