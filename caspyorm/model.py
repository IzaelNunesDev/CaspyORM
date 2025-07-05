# caspyorm/model.py (REVISADO)

from typing import Any, ClassVar, Dict, Optional, List
from typing_extensions import Self
import json

from ._internal.model_construction import ModelMetaclass
from ._internal.schema_sync import sync_table
from ._internal.serialization import generate_pydantic_model, model_to_dict, model_to_json
from .query import QuerySet, get_one, filter_query, save_instance


class Model(metaclass=ModelMetaclass):
    # ... (o resto da classe permanece igual, mas agora os imports apontam para a lógica real)
    # --- Atributos que a metaclasse irá preencher ---
    __table_name__: ClassVar[str]
    __caspy_schema__: ClassVar[Dict[str, Any]]
    model_fields: ClassVar[Dict[str, Any]]

    # --- Métodos de API Pública ---
    def __init__(self, **kwargs: Any):
        self.__dict__["_data"] = {}
        for key, field_obj in self.model_fields.items():
            value = kwargs.get(key)
            if value is None and field_obj.default is not None:
                value = field_obj.default() if callable(field_obj.default) else field_obj.default
            # Sempre chamar to_python para campos de coleção (list, set, dict)
            if hasattr(field_obj, 'python_type') and field_obj.python_type in (list, set, dict):
                value = field_obj.to_python(value)
            elif value is not None and not isinstance(value, field_obj.python_type):
                value = field_obj.to_python(value)
            self.__dict__[key] = value

    def __setattr__(self, key: str, value: Any):
        if key in self.model_fields:
            self.__dict__[key] = value
        else:
            super().__setattr__(key, value)

    def model_dump(self, by_alias: bool = False) -> Dict[str, Any]:
        return model_to_dict(self, by_alias=by_alias)

    def model_dump_json(self, by_alias: bool = False, indent: Optional[int] = None) -> str:
        return model_to_json(self, by_alias=by_alias, indent=indent)

    def save(self) -> Self:
        save_instance(self)
        return self

    @classmethod
    def create(cls, **kwargs: Any) -> Self:
        instance = cls(**kwargs)
        instance.save()
        return instance

    @classmethod
    def get(cls, **kwargs: Any) -> Optional[Self]:
        """Busca um único registro."""
        # A lógica foi movida para query.py, que usa o QuerySet
        return get_one(cls, **kwargs)

    @classmethod
    def filter(cls, **kwargs: Any) -> QuerySet:
        """Inicia uma query com filtros e retorna um QuerySet."""
        return QuerySet(cls).filter(**kwargs)

    @classmethod
    def all(cls) -> QuerySet:
        """Retorna um QuerySet para todos os registros da tabela."""
        return QuerySet(cls)

    # --- Pydantic & FastAPI Integração ---
    @classmethod
    def as_pydantic(cls, name: Optional[str] = None, exclude: Optional[List[str]] = None) -> type:
        """Gera um modelo Pydantic (classe) a partir deste modelo CaspyORM."""
        return generate_pydantic_model(cls, name=name, exclude=exclude or [])

    def to_pydantic_model(self, exclude: Optional[List[str]] = None) -> Any:
        """Converte esta instância do modelo CaspyORM para uma instância Pydantic."""
        PydanticModel = self.as_pydantic(exclude=exclude or [])
        return PydanticModel(**self.model_dump())

    # --- Métodos de Schema ---
    @classmethod
    def sync_table(cls, auto_apply: bool = False, verbose: bool = True):
        sync_table(cls, auto_apply=auto_apply, verbose=verbose)

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={getattr(self, k)!r}" for k in self.model_fields)
        return f"{self.__class__.__name__}({attrs})"

    def delete(self) -> None:
        """Deleta esta instância específica do banco de dados."""
        pk_fields = self.__caspy_schema__['primary_keys']
        if not pk_fields:
            raise RuntimeError("Não é possível deletar um modelo sem chave primária.")
        pk_filters = {field: getattr(self, field) for field in pk_fields}
        from .query import QuerySet
        QuerySet(self.__class__).filter(**pk_filters).delete()
        print(f"DELETADO: {self}")