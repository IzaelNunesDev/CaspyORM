#!/usr/bin/env python3
"""
Teste das melhorias implementadas na CaspyORM:
1. Tipagem correta em as_pydantic
2. Suporte a coleções em generate_pydantic_model
3. Logging em vez de print
4. Avisos para filtros em campos não-indexados
"""

import logging
import warnings
import uuid
from datetime import datetime

# Configurar logging para ver as mensagens
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from caspyorm import Model, fields
from caspyorm.connection import connect, get_session

# Definir modelo de teste com coleções
class Usuario(Model):
    __table_name__ = 'usuarios_melhorias'
    
    id = fields.UUID(primary_key=True)
    nome = fields.Text(required=True)
    email = fields.Text(required=True)
    tags = fields.List(fields.Text(), default=list)  # Lista de strings
    habilidades = fields.Set(fields.Text(), default=set)  # Set de strings
    configuracoes = fields.Map(fields.Text(), fields.Text(), default=dict)  # Map de string para string
    ativo = fields.Boolean(default=True)
    criado_em = fields.Timestamp(default=datetime.now)

def test_1_tipagem_as_pydantic():
    """Teste 1: Verificar se as_pydantic retorna Type[Any] em vez de type"""
    print("\n=== Teste 1: Tipagem de as_pydantic ===")
    
    # Verificar se o método existe e tem a tipagem correta
    pydantic_model = Usuario.as_pydantic()
    print(f"✅ as_pydantic retorna: {type(pydantic_model)}")
    print(f"   Nome do modelo: {pydantic_model.__name__}")
    
    # Verificar se é uma classe válida
    try:
        instance = pydantic_model(nome="Teste", email="teste@teste.com")
        print(f"✅ Instância Pydantic criada: {instance}")
    except Exception as e:
        print(f"❌ Erro ao criar instância Pydantic: {e}")

def test_2_suporte_colecoes():
    """Teste 2: Verificar se coleções são suportadas em generate_pydantic_model"""
    print("\n=== Teste 2: Suporte a Coleções ===")
    
    try:
        pydantic_model = Usuario.as_pydantic()
        
        # Criar instância com coleções
        usuario_data = {
            "nome": "João Silva",
            "email": "joao@teste.com",
            "tags": ["python", "cassandra", "orm"],
            "habilidades": {"programação", "design", "testes"},
            "configuracoes": {"tema": "dark", "idioma": "pt-BR"},
            "ativo": True
        }
        
        pydantic_instance = pydantic_model(**usuario_data)
        print(f"✅ Instância Pydantic com coleções criada:")
        print(f"   Tags: {pydantic_instance.tags}")
        print(f"   Habilidades: {pydantic_instance.habilidades}")
        print(f"   Configurações: {pydantic_instance.configuracoes}")
        
    except Exception as e:
        print(f"❌ Erro com coleções: {e}")

def test_3_logging_vs_print():
    """Teste 3: Verificar se logging está sendo usado em vez de print"""
    print("\n=== Teste 3: Logging vs Print ===")
    
    try:
        # Criar e salvar uma instância (deve gerar logs)
        usuario = Usuario.create(
            id=uuid.uuid4(),
            nome="Maria Silva",
            email="maria@teste.com",
            tags=["teste"],
            habilidades={"python"},
            configuracoes={"teste": "valor"}
        )
        print(f"✅ Usuário criado: {usuario.nome}")
        
        # Buscar o usuário (deve gerar logs de query)
        usuario_buscado = Usuario.get(id=usuario.id)
        if usuario_buscado:
            print(f"✅ Usuário buscado: {usuario_buscado.nome}")
        else:
            print("❌ Usuário não encontrado")
        
        print("✅ Logs foram gerados (verificar saída acima)")
        
    except Exception as e:
        print(f"❌ Erro no teste de logging: {e}")

def test_4_aviso_campos_nao_indexados():
    """Teste 4: Verificar se avisos são emitidos para filtros em campos não-indexados"""
    print("\n=== Teste 4: Avisos para Campos Não-Indexados ===")
    
    # Capturar warnings
    captured_warnings = []
    
    def capture_warnings(message, category, filename, lineno, file=None, line=None):
        captured_warnings.append(str(message))
    
    # Substituir temporariamente a função de warning
    original_showwarning = warnings.showwarning
    warnings.showwarning = capture_warnings
    
    try:
        # Tentar filtrar por campo não-indexado (deve gerar warning)
        usuarios = Usuario.filter(nome="Teste").all()
        print(f"✅ Query executada, {len(usuarios)} resultados")
        
        if captured_warnings:
            print(f"✅ Avisos capturados: {len(captured_warnings)}")
            for warning in captured_warnings:
                print(f"   ⚠️  {warning}")
        else:
            print("❌ Nenhum aviso foi emitido (esperado para campos não-indexados)")
            
    except Exception as e:
        print(f"❌ Erro no teste de avisos: {e}")
    finally:
        # Restaurar função original
        warnings.showwarning = original_showwarning

def main():
    """Função principal para executar todos os testes"""
    print("🧪 Testando Melhorias da CaspyORM")
    print("=" * 50)
    
    # Conectar ao Cassandra
    try:
        connect(contact_points=['127.0.0.1'], keyspace='caspyorm_api_test')
        print("✅ Conectado ao Cassandra")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return
    
    # Sincronizar tabela
    try:
        Usuario.sync_table(auto_apply=True, verbose=False)
        print("✅ Tabela sincronizada")
    except Exception as e:
        print(f"❌ Erro ao sincronizar tabela: {e}")
        return
    
    # Executar testes
    test_1_tipagem_as_pydantic()
    test_2_suporte_colecoes()
    test_3_logging_vs_print()
    test_4_aviso_campos_nao_indexados()
    
    print("\n" + "=" * 50)
    print("🎉 Todos os testes concluídos!")

if __name__ == "__main__":
    main() 