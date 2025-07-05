"""
Modelo de Post usando CaspyORM.
"""
import uuid
from datetime import datetime
from caspyorm import Model, fields

class Post(Model):
    """Modelo de post com CaspyORM."""
    __table_name__ = 'posts'
    
    id = fields.UUID(primary_key=True)
    title = fields.Text(required=True)
    content = fields.Text(required=True)
    author_id = fields.UUID(required=True, index=True)
    tags = fields.List(fields.Text())  # Tags do post
    likes = fields.Set(fields.UUID())  # IDs dos usuários que curtiram
    is_published = fields.Boolean(default=False)
    created_at = fields.Timestamp()  # Sem valor default
    updated_at = fields.Timestamp()  # Sem valor default
    
    @classmethod
    def create_post(cls, title: str, content: str, author_id: uuid.UUID, tags: list = None):
        """Cria um novo post."""
        return cls.create(
            id=uuid.uuid4(),
            title=title,
            content=content,
            author_id=author_id,
            tags=tags if tags is not None else [],
            likes=set(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def add_like(self, user_id: uuid.UUID):
        """Adiciona um like ao post de forma atômica."""
        self.update_collection('likes', add=[user_id])
    
    def remove_like(self, user_id: uuid.UUID):
        """Remove um like do post de forma atômica."""
        self.update_collection('likes', remove=[user_id])
    
    def add_tag(self, tag: str):
        """Adiciona uma tag ao post de forma atômica."""
        self.update_collection('tags', add=[tag])

# Gerar modelo Pydantic para API
PostPydantic = Post.as_pydantic("PostCreate")
PostResponse = Post.as_pydantic("PostResponse") 