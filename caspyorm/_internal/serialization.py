# caspyorm/_internal/serialization.py
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Type, Optional
import logging

# Importação do Model para tipagem
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..model import Model

logger = logging.getLogger(__name__)

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
    def create_model(*args, **kwargs): return None
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
    
    pydantic_fields: Dict[str, Any] = {}
    caspy_fields = model_cls.model_fields  # Usar a propriedade da classe

    for field_name, field_obj in caspy_fields.items():
        if field_name in exclude:
            continue
        
        # Usa o método get_pydantic_type() que implementamos nos fields
        try:
            python_type = field_obj.get_pydantic_type()
        except (ImportError, TypeError) as e:
            logger.warning(f"Não foi possível obter o tipo Pydantic para o campo '{field_name}'. Erro: {e}")
            continue
            
        if field_obj.required:
            pydantic_fields[field_name] = (python_type, ...)
        elif field_obj.default is not None:
            pydantic_fields[field_name] = (python_type, field_obj.default)
        else:
            # Campo opcional sem default
            from typing import Optional as OptionalType
            pydantic_fields[field_name] = (OptionalType[python_type], None)

    model_name = name or f"{model_cls.__name__}Pydantic"
    pydantic_model = create_model(model_name, **pydantic_fields)
    
    if pydantic_model is None:
        raise RuntimeError("Falha ao criar modelo Pydantic")
    
    return pydantic_model 