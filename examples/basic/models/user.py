"""
Modelo de Usuário usando CaspyORM.
"""
import uuid
from datetime import datetime
from caspyorm import Model, fields

class User(Model):
    """Modelo de usuário com CaspyORM."""
    __table_name__ = 'users'
    
    id = fields.UUID(primary_key=True)
    username = fields.Text(required=True)
    email = fields.Text(required=True, index=True)
    full_name = fields.Text()
    is_active = fields.Boolean(default=True)
    tags = fields.List(fields.Text())  # Tags do usuário
    preferences = fields.Map(fields.Text(), fields.Text())  # Preferências como chave-valor
    created_at = fields.Timestamp()  # Sem valor default
    
    @classmethod
    def create_user(cls, username: str, email: str, full_name: str = ""):
        """Cria um novo usuário com ID gerado automaticamente."""
        return cls.create(
            id=uuid.uuid4(),
            username=username,
            email=email,
            full_name=full_name,
            tags=[],
            preferences={},
            created_at=datetime.now()
        )

# Gerar modelo Pydantic para API
UserPydantic = User.as_pydantic("UserCreate")
UserResponse = User.as_pydantic("UserResponse", exclude=["preferences"]) 