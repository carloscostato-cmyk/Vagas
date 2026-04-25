"""
Skill Workflow Manager - Gerenciador de Workflow com Aprovação
Integra com o sistema de agentes para aprovação antes de codar
"""

import subprocess
import os
from typing import List, Dict, Any
from skill_agents_system import SkillAgentsSystem, ChangeRequest

class SkillWorkflowManager:
    """Gerenciador principal do workflow com skill agents"""
    
    def __init__(self):
        self.skill_system = SkillAgentsSystem()
        self.current_changes = []
    
    def ask_and_code(self, description: str, files: List[str], code_changes: List[Dict]) -> bool:
        """
        Workflow completo: pergunta, aprova, codifica, commita, push
        """
        print(f"\nIniciando workflow de codificação skill")
        print(f"Descrição: {description}")
        
        # Passo 1: Perguntar aos agentes
        if not self.skill_system.ask_permission_to_code(description, files):
            print("Workflow interrompido: Permissão negada")
            return False
        
        # Passo 2: Codificar as mudanças
        print("\nCodificando mudanças aprovadas...")
        success = self._apply_code_changes(code_changes)
        
        if not success:
            print("Workflow interrompido: Erro na codificação")
            return False
        
        # Passo 3: Verificação pós-codificação
        print("\nVerificação pós-codificação...")
        if not self._verify_changes():
            print("Workflow interrompido: Verificação falhou")
            return False
        
        # Passo 4: Commit e Push
        print("\nFazendo commit e push...")
        if not self._commit_and_push(description):
            print("Workflow interrompido: Erro no commit/push")
            return False
        
        print("\nWorkflow completado com sucesso!")
        return True
    
    def _apply_code_changes(self, code_changes: List[Dict]) -> bool:
        """Aplica as mudanças de código"""
        try:
            for change in code_changes:
                file_path = change.get("file_path")
                operation = change.get("operation")  # "edit", "create", "delete"
                
                if operation == "edit":
                    old_content = change.get("old_content")
                    new_content = change.get("new_content")
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        current_content = f.read()
                    
                    if old_content not in current_content:
                        print(f"Aviso: Conteúdo antigo não encontrado em {file_path}")
                        continue
                    
                    updated_content = current_content.replace(old_content, new_content)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                        f.write("\n")
                    
                    print(f"Editado: {file_path}")
                
                elif operation == "create":
                    content = change.get("content", "")
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"Criado: {file_path}")
                
                elif operation == "delete":
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"Removido: {file_path}")
                    else:
                        print(f"Aviso: Arquivo não encontrado para remoção: {file_path}")
            
            return True
            
        except Exception as e:
            print(f"Erro ao aplicar mudanças: {e}")
            return False
    
    def _verify_changes(self) -> bool:
        """Verifica se as mudanças foram aplicadas corretamente"""
        try:
            # Verificar sintaxe dos arquivos Python
            python_files = []
            for root, dirs, files in os.walk('.'):
                for file in files:
                    if file.endswith('.py'):
                        python_files.append(os.path.join(root, file))
            
            for py_file in python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    compile(content, py_file, 'exec')
                except SyntaxError as e:
                    print(f"Erro de sintaxe em {py_file}: {e}")
                    return False
            
            # Verificar se sistema ainda funciona
            try:
                import rh_specialist
                print("Verificação de sintaxe Python OK")
                print("Módulo principal importável")
                return True
            except ImportError as e:
                print(f"Erro de importação: {e}")
                return False
                
        except Exception as e:
            print(f"Erro na verificação: {e}")
            return False
    
    def _commit_and_push(self, description: str) -> bool:
        """Faz commit e push das mudanças"""
        try:
            # Add todos os arquivos
            result = subprocess.run(['git', 'add', '.'], 
                                  capture_output=True, text=True, cwd='.')
            if result.returncode != 0:
                print(f"Erro no git add: {result.stderr}")
                return False
            
            # Commit
            commit_msg = f"feat: {description}\n\n[skill-workflow-auto] Changes approved by 5 specialist agents"
            result = subprocess.run(['git', 'commit', '-m', commit_msg], 
                                  capture_output=True, text=True, cwd='.')
            if result.returncode != 0:
                print(f"Erro no git commit: {result.stderr}")
                return False
            
            # Push
            result = subprocess.run(['git', 'push'], 
                                  capture_output=True, text=True, cwd='.')
            if result.returncode != 0:
                print(f"Erro no git push: {result.stderr}")
                return False
            
            print("Commit e push realizados com sucesso")
            return True
            
        except Exception as e:
            print(f"Erro no commit/push: {e}")
            return False
    
    def quick_change(self, file_path: str, old_text: str, new_text: str, description: str) -> bool:
        """Método rápido para mudanças simples"""
        code_change = {
            "file_path": file_path,
            "operation": "edit",
            "old_content": old_text,
            "new_content": new_text
        }
        
        return self.ask_and_code(description, [file_path], [code_change])
    
    def create_file(self, file_path: str, content: str, description: str) -> bool:
        """Método para criar novos arquivos"""
        code_change = {
            "file_path": file_path,
            "operation": "create",
            "content": content
        }
        
        return self.ask_and_code(description, [file_path], [code_change])
    
    def delete_file(self, file_path: str, description: str) -> bool:
        """Método para remover arquivos"""
        code_change = {
            "file_path": file_path,
            "operation": "delete"
        }
        
        return self.ask_and_code(description, [file_path], [code_change])

# Exemplo de uso
def demonstrate_skill_workflow():
    """Demonstra o sistema skill em ação"""
    manager = SkillWorkflowManager()
    
    print("Demonstração do Sistema Skill Agents")
    print("=" * 50)
    
    # Exemplo 1: Mudança simples
    print("\nTestando mudança simples...")
    success = manager.quick_change(
        file_path="test_example.py",
        old_text="# Original comment",
        new_text="# Updated comment with skill approval",
        description="Atualizar comentário de exemplo"
    )
    
    if success:
        print("Demonstração concluída com sucesso!")
    else:
        print("Demonstração falhou")

if __name__ == "__main__":
    demonstrate_skill_workflow()
