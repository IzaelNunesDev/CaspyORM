# CaspyORM

Uma biblioteca Python moderna e assíncrona para trabalhar com Apache Cassandra, inspirada no Django ORM mas otimizada para o modelo de dados do Cassandra.

## 🚀 Características Principais

- **API Familiar**: Sintaxe inspirada no Django ORM
- **Suporte Assíncrono**: Operações assíncronas nativas
- **Modelos Dinâmicos**: Criação de modelos em tempo de execução
- **Integração Pydantic**: Validação e serialização avançadas
- **Performance Otimizada**: Otimizado para o modelo de dados do Cassandra
- **Type Hints**: Suporte completo a type hints

## 📦 Instalação

```bash
pip install caspyorm
```

## 🔧 Configuração Rápida

```python
from caspyorm import Model, connect
from caspyorm.fields import Text, Integer, UUID

# Conectar ao Cassandra
connect(contact_points=['localhost'], keyspace='my_keyspace')

# Definir modelo
class User(Model):
    id = UUID(primary_key=True)
    name = Text(required=True)
    email = Text(index=True)
    age = Integer()

# Sincronizar tabela
User.sync_table()

# Criar usuário
user = User.create(id=uuid.uuid4(), name="João", email="joao@example.com", age=30)
```

## 🎯 Casos de Uso

### Operações Assíncronas
```python
async def main():
    # Criar usuário de forma assíncrona
    user = await User.create_async(
        id=uuid.uuid4(), 
        name="Maria", 
        email="maria@example.com"
    )
    
    # Buscar usuário
    found_user = await User.get_async(email="maria@example.com")
    
    # Atualizar
    await user.update_async(age=25)
```

### Modelos Dinâmicos
```python
# Criar modelo dinamicamente
UserModel = Model.create_model(
    name="DynamicUser",
    fields={
        "id": UUID(primary_key=True),
        "name": Text(required=True),
        "email": Text(index=True),
        "tags": List(Text())
    }
)

# Usar normalmente
user = UserModel(id=uuid.uuid4(), name="João", tags=["dev", "python"])
await user.save_async()
```

## 📚 Documentação

- [Guia Rápido](quickstart.md) - Comece aqui
- [Definição de Modelos](models/definition.md) - Como definir modelos
- [Operações CRUD](queries/crud.md) - Criar, ler, atualizar, deletar
- [Operações Assíncronas](async.md) - Trabalhando com async/await
- [API Reference](api/model.md) - Documentação completa da API

## 🤝 Contribuindo

Contribuições são bem-vindas! Veja o [guia de contribuição](contributing.md) para mais detalhes.

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](../LICENSE) para detalhes. 