# test_pydantic_integration.py
import uuid
from caspyorm import fields, Model, connection

# Conectar ao Cassandra
connection.connect(contact_points=['127.0.0.1'], keyspace='caspyorm_pydantic_test')

# Definir modelo
class Usuario(Model):
    __table_name__ = 'usuarios_pydantic'
    id: fields.UUID = fields.UUID(primary_key=True)
    nome: fields.Text = fields.Text(required=True)
    email: fields.Text = fields.Text(index=True)

# Sincronizar tabela
Usuario.sync_table()

# Testar geração de modelos Pydantic
print("=== Testando Integração com Pydantic ===")

# Gerar modelo Pydantic para entrada (sem ID)
UsuarioIn = Usuario.as_pydantic(name='UsuarioIn', exclude=['id'])
print(f"Modelo Pydantic para entrada: {UsuarioIn}")

# Gerar modelo Pydantic para saída (com todos os campos)
UsuarioOut = Usuario.as_pydantic(name='UsuarioOut')
print(f"Modelo Pydantic para saída: {UsuarioOut}")

# Criar uma instância do modelo CaspyORM
usuario = Usuario.create(
    id=uuid.uuid4(),
    nome="Ada Lovelace",
    email="ada@babbage.com"
)

# Converter para modelo Pydantic
usuario_pydantic = usuario.to_pydantic_model()
print(f"Instância Pydantic: {usuario_pydantic}")
print(f"Dados Pydantic: {usuario_pydantic.model_dump()}")

# Testar validação do modelo Pydantic
try:
    # Isso deve funcionar
    usuario_in = UsuarioIn(nome="Marie Curie", email="marie@radium.com")
    print(f"Validação bem-sucedida: {usuario_in.model_dump()}")
except Exception as e:
    print(f"Erro na validação: {e}")

print("\n✅ Integração com Pydantic funcionando!")

connection.disconnect() 