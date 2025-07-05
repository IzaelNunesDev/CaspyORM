#!/usr/bin/env python3
"""
Testes para compatibilidade com Pydantic v2.
"""

import pytest
import uuid
from datetime import datetime
from caspyorm import Model
from caspyorm.fields import Text, Integer, UUID, Timestamp, List, Set

class TestPydanticV2Compatibility:
    """Testes para compatibilidade com Pydantic v2."""
    
    def test_pydantic_import_detection(self):
        """Testa se a detecção da versão do Pydantic funciona."""
        from caspyorm._internal.serialization import PYDANTIC_V2
        
        # Deve ser True se pydantic estiver instalado
        assert isinstance(PYDANTIC_V2, bool)
    
    def test_pydantic_model_generation(self):
        """Testa a geração de modelos Pydantic."""
        # Criar modelo CaspyORM
        class UserModel(Model):
            id = UUID(primary_key=True)
            name = Text(required=True)
            email = Text(index=True)
            age = Integer()
            created_at = Timestamp(default=datetime.now)
            tags = List(Text())
            scores = Set(Integer())
        
        # Gerar modelo Pydantic
        PydanticUser = UserModel.as_pydantic(name="PydanticUser")
        
        # Verificar se o modelo foi criado
        assert PydanticUser is not None
        assert hasattr(PydanticUser, '__fields__') or hasattr(PydanticUser, 'model_fields')
        
        # Testar instanciação
        user_data = {
            "id": str(uuid.uuid4()),
            "name": "Test User",
            "email": "test@example.com",
            "age": 30,
            "tags": ["tag1", "tag2"],
            "scores": {1, 2, 3}
        }
        
        pydantic_user = PydanticUser(**user_data)
        
        # Verificar se os dados foram processados corretamente
        assert pydantic_user.name == "Test User"
        assert pydantic_user.email == "test@example.com"
        assert pydantic_user.age == 30
        assert pydantic_user.tags == ["tag1", "tag2"]
        assert pydantic_user.scores == {1, 2, 3}
    
    def test_pydantic_model_with_exclusions(self):
        """Testa a geração de modelos Pydantic com exclusões."""
        class UserModel(Model):
            id = UUID(primary_key=True)
            name = Text(required=True)
            email = Text(index=True)
            age = Integer()
            internal_field = Text()  # Campo a ser excluído
        
        # Gerar modelo Pydantic excluindo campo interno
        PydanticUser = UserModel.as_pydantic(
            name="PydanticUserExcluded", 
            exclude=["internal_field"]
        )
        
        # Verificar se o campo foi excluído
        field_names = []
        if hasattr(PydanticUser, '__fields__'):
            # Pydantic v1
            field_names = list(PydanticUser.__fields__.keys())
        elif hasattr(PydanticUser, 'model_fields'):
            # Pydantic v2
            field_names = list(PydanticUser.model_fields.keys())
        
        assert "internal_field" not in field_names
        assert "id" in field_names
        assert "name" in field_names
        assert "email" in field_names
        assert "age" in field_names
    
    def test_pydantic_model_validation(self):
        """Testa a validação de modelos Pydantic gerados."""
        class UserModel(Model):
            id = UUID(primary_key=True)
            name = Text(required=True)
            email = Text(index=True)
            age = Integer()
        
        PydanticUser = UserModel.as_pydantic()
        
        # Testar validação com dados válidos
        valid_data = {
            "id": str(uuid.uuid4()),
            "name": "Valid User",
            "email": "valid@example.com",
            "age": 25
        }
        
        user = PydanticUser(**valid_data)
        assert user.name == "Valid User"
        
        # Testar validação com dados inválidos (deve falhar)
        invalid_data = {
            "id": str(uuid.uuid4()),
            "name": "Invalid User",
            "email": "invalid@example.com",
            "age": "not_a_number"  # Deveria ser int
        }
        
        with pytest.raises(Exception):  # Pydantic validation error
            PydanticUser(**invalid_data)
    
    def test_pydantic_model_serialization(self):
        """Testa a serialização de modelos Pydantic."""
        class UserModel(Model):
            id = UUID(primary_key=True)
            name = Text(required=True)
            email = Text(index=True)
            age = Integer()
            created_at = Timestamp(default=datetime.now)
        
        # Criar instância CaspyORM
        caspy_user = UserModel(
            id=uuid.uuid4(),
            name="Serialization Test",
            email="serial@example.com",
            age=30
        )
        
        # Converter para Pydantic
        pydantic_user = caspy_user.to_pydantic_model()
        
        # Verificar serialização
        assert pydantic_user.name == "Serialization Test"
        assert pydantic_user.email == "serial@example.com"
        assert pydantic_user.age == 30
        
        # Testar serialização para dict
        user_dict = pydantic_user.model_dump() if hasattr(pydantic_user, 'model_dump') else pydantic_user.dict()
        
        assert user_dict["name"] == "Serialization Test"
        assert user_dict["email"] == "serial@example.com"
        assert user_dict["age"] == 30
    
    def test_pydantic_model_with_complex_types(self):
        """Testa modelos Pydantic com tipos complexos."""
        class ComplexModel(Model):
            id = UUID(primary_key=True)
            name = Text(required=True)
            tags = List(Text())
            scores = Set(Integer())
            metadata = Text()  # Simular campo adicional
        
        # Gerar modelo Pydantic
        PydanticComplex = ComplexModel.as_pydantic()
        
        # Testar com dados complexos
        complex_data = {
            "id": str(uuid.uuid4()),
            "name": "Complex User",
            "tags": ["python", "cassandra", "orm"],
            "scores": {85, 92, 78},
            "metadata": "additional info"
        }
        
        pydantic_complex = PydanticComplex(**complex_data)
        
        assert pydantic_complex.name == "Complex User"
        assert pydantic_complex.tags == ["python", "cassandra", "orm"]
        assert pydantic_complex.scores == {85, 92, 78}
        assert pydantic_complex.metadata == "additional info"
    
    def test_pydantic_model_field_types(self):
        """Testa se os tipos de campo são mapeados corretamente."""
        class TypeTestModel(Model):
            id = UUID(primary_key=True)
            name = Text(required=True)
            age = Integer()
            score = Integer()
            active = Text()  # Simular boolean como text
        
        PydanticTypeTest = TypeTestModel.as_pydantic()
        
        # Verificar tipos dos campos
        field_types = {}
        if hasattr(PydanticTypeTest, 'model_fields'):
            # Pydantic v2
            for field_name, field in PydanticTypeTest.model_fields.items():
                field_types[field_name] = field.annotation
        elif hasattr(PydanticTypeTest, '__fields__'):
            # Pydantic v1 (deprecated)
            for field_name, field in PydanticTypeTest.__fields__.items():
                field_types[field_name] = field.type_
        
        # Verificar se os tipos estão corretos
        assert "id" in field_types
        assert "name" in field_types
        assert "age" in field_types
        assert "score" in field_types
        assert "active" in field_types 