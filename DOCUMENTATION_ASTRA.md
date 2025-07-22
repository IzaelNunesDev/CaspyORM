### Conectando ao Astra DB (DataStax)

O CaspyORM oferece suporte de primeira classe para o Astra DB, o banco de dados como serviço da DataStax. A conexão é simplificada através do uso do **Secure Connect Bundle**.

**Passos para Conectar:**

1.  **Baixe o Secure Connect Bundle:** Faça o download do arquivo ZIP do bundle de conexão diretamente do painel do seu banco de dados no Astra DB.
2.  **Configure as Credenciais:** Você precisará do seu `Client ID` e `Client Secret` (gerados como um token no Astra DB).
3.  **Use `connection.connect()`:** Passe o caminho para o seu bundle e suas credenciais para o método de conexão.

**Exemplo de Código:**

```python
import os
from caspyorm import connection, models, fields

# --- Configuração --- 
A_DB_BUNDLE_PATH = "/caminho/para/seu/secure-connect-database.zip"
ASTRA_DB_CLIENT_ID = "seu-client-id"  # Geralmente 'token'
ASTRA_DB_CLIENT_SECRET = "AstraCS:seu-token-completo" # O token gerado no Astra
ASTRA_DB_KEYSPACE = "seu_keyspace"

# --- Conexão ---
def connect_to_astra():
    try:
        connection.connect(
            keyspace=ASTRA_DB_KEYSPACE,
            secure_connect_bundle=ASTRA_DB_BUNDLE_PATH,
            username=ASTRA_DB_CLIENT_ID,
            password=ASTRA_DB_CLIENT_SECRET,
            protocol_version=4  # Importante para compatibilidade
        )
        print("Conexão com Astra DB estabelecida com sucesso!")
    except Exception as e:
        print(f"Falha ao conectar: {e}")

# --- Exemplo de Uso ---
class MeuModelo(models.Model):
    __table_name__ = 'meu_modelo_astra'
    id = fields.UUID(primary_key=True)
    nome = fields.Text()

# Conectar e sincronizar
connect_to_astra()
MeuModelo.sync_table()

# Criar um novo registro
novo_item = MeuModelo.create(nome="Teste Astra DB")
print(f"Item criado: {novo_item.id}")
```

**Pontos Importantes:**

-   Não é necessário especificar `contact_points` ou `port` ao usar o `secure_connect_bundle`.
-   O CaspyORM lida com a configuração SSL/TLS e a topologia do cluster internamente quando o bundle é fornecido.
-   Certifique-se de que a dependência `cassandra-driver` esteja na versão `4.0.0` ou superior no seu `pyproject.toml` para garantir total compatibilidade.
