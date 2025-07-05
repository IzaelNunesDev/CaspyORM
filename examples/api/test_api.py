#!/usr/bin/env python3
"""
Script de teste automatizado para a CaspyORM Demo API.
"""
import requests
import json
import time
from typing import Dict, Any

class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
    
    def log_test(self, test_name: str, success: bool, details: Dict[str, Any] = None):
        """Registra o resultado de um teste."""
        result = {
            "test": test_name,
            "success": success,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "details": details or {}
        }
        self.results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {json.dumps(details, indent=2, ensure_ascii=False)}")
        print()
    
    def test_health_check(self):
        """Testa o endpoint de health check."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            success = response.status_code == 200
            details = response.json() if success else {"status_code": response.status_code}
            self.log_test("Health Check", success, details)
            return success
        except Exception as e:
            self.log_test("Health Check", False, {"error": str(e)})
            return False
    
    def test_setup_demo_data(self):
        """Testa a configuração de dados de demonstração."""
        try:
            response = self.session.get(f"{self.base_url}/demo/setup")
            success = response.status_code == 200
            details = response.json() if success else {"status_code": response.status_code}
            self.log_test("Setup Demo Data", success, details)
            return success
        except Exception as e:
            self.log_test("Setup Demo Data", False, {"error": str(e)})
            return False
    
    def test_list_users(self):
        """Testa a listagem de usuários."""
        try:
            response = self.session.get(f"{self.base_url}/users/")
            success = response.status_code == 200
            if success:
                users = response.json()
                details = {"count": len(users), "sample_user": users[0] if users else None}
            else:
                details = {"status_code": response.status_code}
            self.log_test("List Users", success, details)
            return success
        except Exception as e:
            self.log_test("List Users", False, {"error": str(e)})
            return False
    
    def test_list_posts(self):
        """Testa a listagem de posts."""
        try:
            response = self.session.get(f"{self.base_url}/posts/?published_only=false")
            success = response.status_code == 200
            if success:
                posts = response.json()
                details = {"count": len(posts), "sample_post": posts[0] if posts else None}
            else:
                details = {"status_code": response.status_code}
            self.log_test("List Posts", success, details)
            return success
        except Exception as e:
            self.log_test("List Posts", False, {"error": str(e)})
            return False
    
    def test_user_stats(self):
        """Testa as estatísticas de usuários."""
        try:
            response = self.session.get(f"{self.base_url}/users/stats/count")
            success = response.status_code == 200
            details = response.json() if success else {"status_code": response.status_code}
            self.log_test("User Stats", success, details)
            return success
        except Exception as e:
            self.log_test("User Stats", False, {"error": str(e)})
            return False
    
    def test_post_stats(self):
        """Testa as estatísticas de posts."""
        try:
            response = self.session.get(f"{self.base_url}/posts/stats/count")
            success = response.status_code == 200
            details = response.json() if success else {"status_code": response.status_code}
            self.log_test("Post Stats", success, details)
            return success
        except Exception as e:
            self.log_test("Post Stats", False, {"error": str(e)})
            return False
    
    def test_demo_stats(self):
        """Testa as estatísticas detalhadas de demonstração."""
        try:
            response = self.session.get(f"{self.base_url}/demo/stats")
            success = response.status_code == 200
            details = response.json() if success else {"status_code": response.status_code}
            self.log_test("Demo Stats", success, details)
            return success
        except Exception as e:
            self.log_test("Demo Stats", False, {"error": str(e)})
            return False
    
    def test_endpoint_tests(self):
        """Testa os endpoints de teste da API."""
        try:
            response = self.session.get(f"{self.base_url}/demo/test")
            success = response.status_code == 200
            details = response.json() if success else {"status_code": response.status_code}
            self.log_test("API Endpoint Tests", success, details)
            return success
        except Exception as e:
            self.log_test("API Endpoint Tests", False, {"error": str(e)})
            return False
    
    def test_user_search(self):
        """Testa operações de busca de usuários."""
        try:
            response = self.session.get(f"{self.base_url}/users/test/search")
            success = response.status_code == 200
            details = response.json() if success else {"status_code": response.status_code}
            self.log_test("User Search Operations", success, details)
            return success
        except Exception as e:
            self.log_test("User Search Operations", False, {"error": str(e)})
            return False
    
    def test_user_bulk(self):
        """Testa operações em lote de usuários."""
        try:
            response = self.session.get(f"{self.base_url}/users/test/bulk")
            success = response.status_code == 200
            details = response.json() if success else {"status_code": response.status_code}
            self.log_test("User Bulk Operations", success, details)
            return success
        except Exception as e:
            self.log_test("User Bulk Operations", False, {"error": str(e)})
            return False
    
    def test_post_collections(self):
        """Testa operações com coleções de posts."""
        try:
            response = self.session.get(f"{self.base_url}/posts/test/collections")
            success = response.status_code == 200
            details = response.json() if success else {"status_code": response.status_code}
            self.log_test("Post Collection Operations", success, details)
            return success
        except Exception as e:
            self.log_test("Post Collection Operations", False, {"error": str(e)})
            return False
    
    def test_post_likes(self):
        """Testa operações de like em posts."""
        try:
            response = self.session.get(f"{self.base_url}/posts/test/likes")
            success = response.status_code == 200
            details = response.json() if success else {"status_code": response.status_code}
            self.log_test("Post Like Operations", success, details)
            return success
        except Exception as e:
            self.log_test("Post Like Operations", False, {"error": str(e)})
            return False
    
    def test_post_tags(self):
        """Testa operações de tags em posts."""
        try:
            response = self.session.get(f"{self.base_url}/posts/test/tags")
            success = response.status_code == 200
            details = response.json() if success else {"status_code": response.status_code}
            self.log_test("Post Tag Operations", success, details)
            return success
        except Exception as e:
            self.log_test("Post Tag Operations", False, {"error": str(e)})
            return False
    
    def run_all_tests(self):
        """Executa todos os testes."""
        print("🚀 Iniciando testes da CaspyORM Demo API...")
        print("=" * 50)
        
        tests = [
            self.test_health_check,
            self.test_setup_demo_data,
            self.test_list_users,
            self.test_list_posts,
            self.test_user_stats,
            self.test_post_stats,
            self.test_demo_stats,
            self.test_endpoint_tests,
            self.test_user_search,
            self.test_user_bulk,
            self.test_post_collections,
            self.test_post_likes,
            self.test_post_tags
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print("=" * 50)
        print(f"📊 Resumo dos Testes:")
        print(f"   ✅ Passou: {passed}")
        print(f"   ❌ Falhou: {total - passed}")
        print(f"   📈 Taxa de Sucesso: {(passed/total)*100:.1f}%")
        
        # Salvar resultados em arquivo
        with open("test_results.json", "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": total - passed,
                    "success_rate": (passed/total)*100
                },
                "results": self.results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Resultados salvos em: test_results.json")
        
        return passed == total

if __name__ == "__main__":
    tester = APITester()
    success = tester.run_all_tests()
    exit(0 if success else 1) 