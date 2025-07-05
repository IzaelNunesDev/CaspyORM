#!/usr/bin/env python3
"""
Exemplo demonstrando as melhorias implementadas:
1. Validação Assíncrona Parcial - save_instance_async()
2. Modelos Dinâmicos & Reflection - Model.create_model()
"""

import asyncio
import uuid
from datetime import datetime
from caspyorm import Model
from caspyorm.fields import Text, Integer, UUID, Timestamp, List, Set
from caspyorm.connection import connect, connect_async

# Configuração da conexão
connect(contact_points=['localhost'], keyspace='test_keyspace')

async def main():
    print("🚀 Demonstração das Melhorias CaspyORM")
    print("=" * 50)
    
    # 1. Criação Dinâmica de Modelos
    print("\n1️⃣ Criação Dinâmica de Modelos")
    print("-" * 30)
    
    # Criando um modelo dinamicamente
    UserModel = Model.create_model(
        name="DynamicUser",
        fields={
            "id": UUID(primary_key=True),
            "name": Text(required=True),
            "email": Text(index=True),
            "age": Integer(),
            "created_at": Timestamp(default=datetime.now),
            "tags": List(Text()),
            "roles": Set(Text())
        },
        table_name="dynamic_users"
    )
    
    print(f"✅ Modelo criado dinamicamente: {UserModel.__name__}")
    print(f"   Tabela: {UserModel.__table_name__}")
    print(f"   Campos: {list(UserModel.model_fields.keys())}")
    print(f"   Primary Keys: {UserModel.__caspy_schema__['primary_keys']}")
    
    # Sincronizar a tabela
    await UserModel.sync_table_async(auto_apply=True)
    print("✅ Tabela sincronizada")
    
    # 2. Validação Assíncrona Parcial
    print("\n2️⃣ Validação Assíncrona Parcial")
    print("-" * 30)
    
    # Criar instância com dados
    user_data = {
        "id": uuid.uuid4(),
        "name": "João Silva",
        "email": "joao@example.com",
        "age": 30,
        "tags": ["desenvolvedor", "python"],
        "roles": {"user", "admin"}
    }
    
    user = UserModel(**user_data)
    print(f"✅ Instância criada: {user}")
    
    # Salvar de forma assíncrona (agora usa save_instance_async internamente)
    await user.save_async()
    print("✅ Instância salva de forma assíncrona")
    
    # 3. Operações CRUD Assíncronas
    print("\n3️⃣ Operações CRUD Assíncronas")
    print("-" * 30)
    
    # Buscar usuário
    found_user = await UserModel.get_async(id=user.id)
    print(f"✅ Usuário encontrado: {found_user}")
    
    # Atualizar usuário
    await user.update_async(age=31, tags=["desenvolvedor", "python", "senior"])
    print("✅ Usuário atualizado de forma assíncrona")
    
    # Buscar novamente para ver as mudanças
    updated_user = await UserModel.get_async(id=user.id)
    print(f"✅ Usuário após atualização: {updated_user}")
    
    # 4. Criação em Lote Assíncrona
    print("\n4️⃣ Criação em Lote Assíncrona")
    print("-" * 30)
    
    # Criar múltiplos usuários
    users_to_create = []
    for i in range(3):
        user_instance = UserModel(
            id=uuid.uuid4(),
            name=f"Usuário {i+1}",
            email=f"user{i+1}@example.com",
            age=25 + i,
            tags=[f"tag{i+1}"],
            roles={"user"}
        )
        users_to_create.append(user_instance)
    
    # Salvar em lote (assíncrono)
    await UserModel.bulk_create_async(users_to_create)
    print(f"✅ {len(users_to_create)} usuários criados em lote")
    
    # 5. Query Assíncrona
    print("\n5️⃣ Query Assíncrona")
    print("-" * 30)
    
    # Buscar todos os usuários
    all_users = await UserModel.all().all_async()
    print(f"✅ Total de usuários: {len(all_users)}")
    
    # Filtrar usuários
    python_devs = await UserModel.filter(tags__contains="python").all_async()
    print(f"✅ Desenvolvedores Python: {len(python_devs)}")
    
    # 6. Limpeza
    print("\n6️⃣ Limpeza")
    print("-" * 30)
    
    # Deletar todos os usuários criados
    for user_instance in all_users:
        await user_instance.delete_async()
    
    print("✅ Todos os usuários deletados")
    
    print("\n🎉 Demonstração concluída com sucesso!")

if __name__ == "__main__":
    asyncio.run(main()) 