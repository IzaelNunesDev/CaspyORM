# examples/cli_demo.py

"""
Exemplo de demonstração da CLI CaspyORM.
Este arquivo mostra como usar a CLI para interagir com modelos.
"""

import uuid
from datetime import datetime
from caspyorm import Model, fields, connection

# --- Modelos de Exemplo ---

class User(Model):
    __table_name__ = "users"
    
    user_id = fields.UUID(primary_key=True)
    username = fields.Text(partition_key=True)
    email = fields.Text(index=True)
    full_name = fields.Text()
    is_active = fields.Boolean(default=True)
    tags = fields.List(fields.Text())
    created_at = fields.Timestamp()

class Post(Model):
    __table_name__ = "posts"
    
    post_id = fields.UUID(primary_key=True)
    title = fields.Text(required=True)
    content = fields.Text()
    author_id = fields.UUID(index=True)
    tags = fields.List(fields.Text())
    likes = fields.Set(fields.UUID())
    is_published = fields.Boolean(default=False)
    created_at = fields.Timestamp()

# --- Função de Setup ---

async def setup_demo_data():
    """Configura dados de demonstração para testar a CLI."""
    try:
        # Conectar ao Cassandra
        await connection.connect_async(['localhost'], 'caspyorm_demo')
        
        # TODO: Sincronizar tabelas quando necessário
        pass
        
        # Criar usuários de exemplo
        users = [
            await User.create_async(
                user_id=uuid.uuid4(),
                username="joao_silva",
                email="joao@example.com",
                full_name="João Silva",
                tags=["python", "developer"],
                created_at=datetime.now()
            ),
            await User.create_async(
                user_id=uuid.uuid4(),
                username="maria_santos",
                email="maria@example.com",
                full_name="Maria Santos",
                tags=["designer", "ui/ux"],
                created_at=datetime.now()
            ),
            await User.create_async(
                user_id=uuid.uuid4(),
                username="pedro_costa",
                email="pedro@example.com",
                full_name="Pedro Costa",
                tags=["python", "data-science"],
                is_active=False,
                created_at=datetime.now()
            )
        ]
        
        # Criar posts de exemplo
        posts = [
            await Post.create_async(
                post_id=uuid.uuid4(),
                title="Introdução ao CaspyORM",
                content="CaspyORM é um ORM moderno para Cassandra...",
                author_id=users[0].user_id,
                tags=["caspyorm", "cassandra", "python"],
                is_published=True,
                created_at=datetime.now()
            ),
            await Post.create_async(
                post_id=uuid.uuid4(),
                title="Design de APIs Assíncronas",
                content="Como criar APIs eficientes com async/await...",
                author_id=users[1].user_id,
                tags=["api", "async", "fastapi"],
                is_published=True,
                created_at=datetime.now()
            ),
            await Post.create_async(
                post_id=uuid.uuid4(),
                title="Rascunho: Machine Learning com Python",
                content="Este é um rascunho sobre ML...",
                author_id=users[2].user_id,
                tags=["ml", "python", "data-science"],
                is_published=False,
                created_at=datetime.now()
            )
        ]
        
        print("✅ Dados de demonstração criados com sucesso!")
        print(f"   - {len(users)} usuários criados")
        print(f"   - {len(posts)} posts criados")
        print("\n📋 Exemplos de comandos CLI:")
        print("   export CASPY_MODELS_PATH='examples.cli_demo'")
        print("   caspy models")
        print("   caspy user get --filter username=joao_silva")
        print("   caspy user filter --filter is_active=true")
        print("   caspy post count --filter is_published=true")
        print("   caspy post filter --filter author_id=<user_id> --limit 5")
        
    except Exception as e:
        print(f"❌ Erro ao configurar dados: {e}")
    finally:
        try:
            await connection.disconnect_async()
        except:
            pass

if __name__ == "__main__":
    import asyncio
    asyncio.run(setup_demo_data()) 