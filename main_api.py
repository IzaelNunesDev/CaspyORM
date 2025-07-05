# main_api.py

import uuid
import logging
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException

from caspyorm import fields, Model, connection

# Configurar logging
logger = logging.getLogger("caspyorm.api")

# --- Configuração da CaspyORM ---
connection.connect(contact_points=['127.0.0.1'], keyspace='caspyorm_api_test')

class Usuario(Model):
    __table_name__ = 'usuarios_api' # Nova tabela para o teste da API
    id: fields.UUID = fields.UUID(primary_key=True)
    nome: fields.Text = fields.Text(required=True)
    email: fields.Text = fields.Text(index=True)

# Sincroniza a tabela ao iniciar a aplicação
Usuario.sync_table()

# --- Geração dos Modelos Pydantic para a API ---
# Modelo para criar um usuário (não precisa de ID, o DB gera)
UsuarioIn = Usuario.as_pydantic(name='UsuarioIn', exclude=['id'])

# Modelo para retornar um usuário (inclui todos os campos)
UsuarioOut = Usuario.as_pydantic(name='UsuarioOut')


# --- Aplicação FastAPI ---
app = FastAPI(
    title="CaspyORM API Demo",
    description="Demonstração da integração da CaspyORM com FastAPI.",
    version="1.0.0"
)

@app.post("/usuarios/", response_model=UsuarioOut, status_code=201)
def criar_usuario(usuario_in: UsuarioIn):
    """
    Cria um novo usuário no banco de dados.
    """
    novo_id = uuid.uuid4()
    # FastAPI já validou `usuario_in` usando o modelo Pydantic gerado
    # Agora criamos a instância da CaspyORM
    novo_usuario = Usuario.create(id=novo_id, **usuario_in.model_dump())
    return novo_usuario.to_pydantic_model() # Converte a instância CaspyORM para Pydantic para a resposta

@app.get("/usuarios/{usuario_id}", response_model=UsuarioOut)
def ler_usuario(usuario_id: uuid.UUID):
    """
    Busca um usuário pelo seu ID.
    """
    usuario = Usuario.get(id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario.to_pydantic_model()

@app.get("/usuarios/", response_model=List[Any])
def listar_usuarios():
    """
    Lista todos os usuários.
    (NOTA: `all()` ainda não está totalmente implementado, então pode retornar uma lista vazia
    ou precisar de um `ALLOW FILTERING` para funcionar no Cassandra.)
    """
    # Vamos simular por enquanto, já que `all()` não está pronto.
    # Em uma implementação real, seria:
    # usuarios = Usuario.all()
    # return [u.to_pydantic_model() for u in usuarios]
    raise HTTPException(status_code=501, detail="Listagem de todos os usuários ainda não implementada.")

@app.get("/")
def root():
    """
    Endpoint raiz com informações sobre a API.
    """
    return {
        "message": "CaspyORM API Demo",
        "description": "API de demonstração da integração CaspyORM + FastAPI",
        "docs": "/docs",
        "endpoints": {
            "criar_usuario": "POST /usuarios/",
            "buscar_usuario": "GET /usuarios/{id}",
            "listar_usuarios": "GET /usuarios/"
        }
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Para iniciar a API, execute: uvicorn main_api:app --reload")
    logger.info("Documentação disponível em: http://127.0.0.1:8000/docs")
else:
    logger.info("Para iniciar a API, execute: uvicorn main_api:app --reload") 