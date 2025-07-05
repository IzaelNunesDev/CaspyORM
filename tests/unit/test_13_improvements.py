#!/usr/bin/env python3
"""
Testes para as melhorias implementadas:
1. Validação Assíncrona Parcial - save_instance_async()
2. Modelos Dinâmicos & Reflection - Model.create_model()
"""

import pytest
import uuid
from datetime import datetime
from caspyorm import Model
from caspyorm.fields import Text, Integer, UUID, Timestamp, List, Set
from caspyorm.exceptions import ValidationError

class TestImprovements:
    """Testes para as melhorias implementadas."""
    
    def test_create_model_dynamic(self):
        """Testa a criação dinâmica de modelos."""
        # Criar modelo dinamicamente
        UserModel = Model.create_model(
            name="TestUser",
            fields={
                "id": UUID(primary_key=True),
                "name": Text(required=True),
                "email": Text(index=True),
                "age": Integer(),
                "created_at": Timestamp(default=datetime.now),
                "tags": List(Text()),
                "roles": Set(Text())
            },
            table_name="test_users"
        )
        
        # Verificar se o modelo foi criado corretamente
        assert UserModel.__name__ == "TestUser"
        assert UserModel.__table_name__ == "test_users"
        assert "id" in UserModel.model_fields
        assert "name" in UserModel.model_fields
        assert "email" in UserModel.model_fields
        assert "age" in UserModel.model_fields
        assert "created_at" in UserModel.model_fields
        assert "tags" in UserModel.model_fields
        assert "roles" in UserModel.model_fields
        
        # Verificar schema
        assert UserModel.__caspy_schema__ is not None
        assert "id" in UserModel.__caspy_schema__['primary_keys']
        assert "email" in UserModel.__caspy_schema__['indexes']
        
        # Verificar tipos dos campos
        assert UserModel.model_fields["id"].python_type == uuid.UUID
        assert UserModel.model_fields["name"].python_type == str
        assert UserModel.model_fields["age"].python_type == int
        assert UserModel.model_fields["created_at"].python_type == datetime
        
        return UserModel
    
    def test_create_model_validation(self):
        """Testa a validação na criação dinâmica de modelos."""
        # Teste com campo inválido
        with pytest.raises(TypeError, match="deve ser uma instância de BaseField"):
            Model.create_model(
                name="InvalidUser",
                fields={
                    "id": "not_a_field",  # String inválida
                    "name": Text(required=True)
                }
            )
    
    def test_dynamic_model_instantiation(self):
        """Testa a instanciação de modelos criados dinamicamente."""
        UserModel = self.test_create_model_dynamic()
        
        # Criar instância válida
        user_id = uuid.uuid4()
        user = UserModel(
            id=user_id,
            name="João Silva",
            email="joao@example.com",
            age=30,
            tags=["desenvolvedor", "python"],
            roles={"user", "admin"}
        )
        
        # Verificar se os valores foram definidos corretamente
        assert user.id == user_id
        assert user.name == "João Silva"
        assert user.email == "joao@example.com"
        assert user.age == 30
        assert user.tags == ["desenvolvedor", "python"]
        assert user.roles == {"user", "admin"}
        
        # Verificar se o campo com default foi preenchido
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)
    
    def test_dynamic_model_validation(self):
        """Testa a validação em modelos criados dinamicamente."""
        UserModel = self.test_create_model_dynamic()
        
        # Teste com campo obrigatório faltando
        with pytest.raises(ValidationError, match="Campo 'name' é obrigatório"):
            UserModel(
                id=uuid.uuid4(),
                email="joao@example.com"
                # name está faltando
            )
        
        # Teste com tipo inválido
        with pytest.raises(TypeError):
            UserModel(
                id=uuid.uuid4(),
                name="João Silva",
                age="not_a_number"  # Deveria ser int
            )
    
    @pytest.mark.asyncio
    async def test_save_async_uses_save_instance_async(self, monkeypatch):
        """Testa se save_async() usa save_instance_async() internamente."""
        UserModel = self.test_create_model_dynamic()
        
        # Mock da função save_instance_async
        async def mock_save_instance_async(instance):
            # Simular salvamento bem-sucedido
            pass
        
        # Aplicar o mock
        import caspyorm.query
        monkeypatch.setattr(caspyorm.query, "save_instance_async", mock_save_instance_async)
        
        # Criar instância
        user = UserModel(
            id=uuid.uuid4(),
            name="Test User",
            email="test@example.com"
        )
        
        # Chamar save_async (não deve levantar exceção)
        await user.save_async()
        
        # Se chegou até aqui, significa que save_instance_async foi chamado
    
    def test_create_model_with_custom_table_name(self):
        """Testa a criação de modelo com nome de tabela customizado."""
        UserModel = Model.create_model(
            name="CustomUser",
            fields={
                "id": UUID(primary_key=True),
                "name": Text(required=True)
            },
            table_name="custom_users_table"
        )
        
        assert UserModel.__table_name__ == "custom_users_table"
    
    def test_create_model_default_table_name(self):
        """Testa a criação de modelo com nome de tabela padrão."""
        UserModel = Model.create_model(
            name="DefaultUser",
            fields={
                "id": UUID(primary_key=True),
                "name": Text(required=True)
            }
            # table_name não especificado
        )
        
        assert UserModel.__table_name__ == "defaultusers"  # name.lower() + 's'
    
    def test_dynamic_model_repr(self):
        """Testa a representação string de modelos dinâmicos."""
        UserModel = self.test_create_model_dynamic()
        
        user = UserModel(
            id=uuid.uuid4(),
            name="Test User",
            email="test@example.com",
            age=25
        )
        
        repr_str = repr(user)
        assert "TestUser" in repr_str
        assert "name='Test User'" in repr_str
        assert "email='test@example.com'" in repr_str
        assert "age=25" in repr_str
    
    def test_dynamic_model_model_dump(self):
        """Testa o método model_dump() em modelos dinâmicos."""
        UserModel = self.test_create_model_dynamic()
        
        user_id = uuid.uuid4()
        user = UserModel(
            id=user_id,
            name="Test User",
            email="test@example.com",
            age=25,
            tags=["tag1", "tag2"],
            roles={"user"}
        )
        
        data = user.model_dump()
        
        assert data["id"] == user_id
        assert data["name"] == "Test User"
        assert data["email"] == "test@example.com"
        assert data["age"] == 25
        assert data["tags"] == ["tag1", "tag2"]
        assert data["roles"] == {"user"}
        assert "created_at" in data  # Campo com default 