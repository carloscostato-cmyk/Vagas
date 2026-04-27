"""
Skill Agents System - Sistema de Agentes Especialistas
2 Agentes de Manutenção + 3 Agentes de Review
"""

import os
import subprocess
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class AgentType(Enum):
    MAINTENANCE = "maintenance"
    REVIEW = "review"

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

@dataclass
class AgentDecision:
    agent_name: str
    agent_type: AgentType
    decision: ApprovalStatus
    reasoning: str
    confidence: float  # 0.0 to 1.0

@dataclass
class ChangeRequest:
    description: str
    files_to_modify: List[str]
    risk_level: str  # "low", "medium", "high"
    urgency: str  # "low", "medium", "high"

class MaintenanceAgent:
    """Agente especialista em manutenção do sistema"""
    
    def __init__(self, agent_id: int):
        self.agent_id = agent_id
        self.agent_name = f"MaintenanceAgent-{agent_id}"
    
    def check_system_stability(self) -> Dict[str, bool]:
        """Verifica estabilidade do sistema atual"""
        checks = {
            "telegram_bot_running": self._check_telegram_bot(),
            "github_actions_working": self._check_github_actions(),
            "environment_variables": self._check_env_vars(),
            "dependencies_installed": self._check_dependencies(),
            "database_files_ok": self._check_database_files()
        }
        return checks
    
    def _check_telegram_bot(self) -> bool:
        """Verifica se bot Telegram está rodando"""
        try:
            # Verificar se há processo do bot rodando
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                  capture_output=True, text=True)
            return 'telegram_agent.py' in result.stdout.lower()
        except:
            return False
    
    def _check_github_actions(self) -> bool:
        """Verifica se workflows do GitHub Actions estão OK"""
        try:
            workflow_path = ".github/workflows/hr_agent.yml"
            return os.path.exists(workflow_path)
        except:
            return False
    
    def _check_env_vars(self) -> bool:
        """Verifica variáveis de ambiente"""
        required_vars = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
        return all(var in os.environ for var in required_vars)
    
    def _check_dependencies(self) -> bool:
        """Verifica dependências instaladas"""
        try:
            import requests
            import bs4
            return True
        except ImportError:
            return False
    
    def _check_database_files(self) -> bool:
        """Verifica integridade dos arquivos de dados"""
        try:
            files = ["applications.json", "run_summary.json"]
            return all(os.path.exists(f) for f in files)
        except:
            return False
    
    def approve_change(self, change_request: ChangeRequest) -> AgentDecision:
        """Aprova ou rejeita mudança baseado em estabilidade"""
        stability = self.check_system_stability()
        stable_score = sum(stability.values()) / len(stability)
        
        if stable_score < 0.8:
            return AgentDecision(
                agent_name=self.agent_name,
                agent_type=AgentType.MAINTENANCE,
                decision=ApprovalStatus.REJECTED,
                reasoning=f"Sistema instável (score: {stable_score:.2f}). Risco de quebra.",
                confidence=0.9
            )
        
        if change_request.risk_level == "high" and stable_score < 0.95:
            return AgentDecision(
                agent_name=self.agent_name,
                agent_type=AgentType.MAINTENANCE,
                decision=ApprovalStatus.REJECTED,
                reasoning="Alto risco + sistema não 100% estável",
                confidence=0.8
            )
        
        return AgentDecision(
            agent_name=self.agent_name,
            agent_type=AgentType.MAINTENANCE,
            decision=ApprovalStatus.APPROVED,
            reasoning=f"Sistema estável (score: {stable_score:.2f}). Mudança segura.",
            confidence=0.8
        )

class ReviewAgent:
    """Agente especialista em code review"""
    
    def __init__(self, agent_id: int, specialty: str):
        self.agent_id = agent_id
        self.agent_name = f"ReviewAgent-{agent_id}-{specialty}"
        self.specialty = specialty
    
    def analyze_change(self, change_request: ChangeRequest) -> AgentDecision:
        """Analisa mudança baseado na especialidade"""
        if self.specialty == "bugs":
            return self._review_for_bugs(change_request)
        elif self.specialty == "security":
            return self._review_for_security(change_request)
        elif self.specialty == "stability_guard":
            return self._review_for_stability_guard(change_request)
        else:  # patterns
            return self._review_for_patterns(change_request)

    def _review_for_stability_guard(self, change_request: ChangeRequest) -> AgentDecision:
        """Guardiao: bloqueia mudancas em arquivos estaveis sem justificativa explicita."""
        protected_files = {"rh_specialist.py", "telegram_agent.py", "telegram_notifier.py"}
        touched_protected = [f for f in change_request.files_to_modify if f in protected_files]

        if touched_protected:
            return AgentDecision(
                agent_name=self.agent_name,
                agent_type=AgentType.REVIEW,
                decision=ApprovalStatus.REJECTED,
                reasoning=(
                    "Mudanca bloqueada pelo guardiao de estabilidade em componentes funcionais: "
                    + ", ".join(touched_protected)
                ),
                confidence=0.95,
            )

        return AgentDecision(
            agent_name=self.agent_name,
            agent_type=AgentType.REVIEW,
            decision=ApprovalStatus.APPROVED,
            reasoning="Nenhum componente estavel foi alterado.",
            confidence=0.95,
        )
    
    def _review_for_bugs(self, change_request: ChangeRequest) -> AgentDecision:
        """Review focado em bugs e lógica"""
        risk_factors = []
        
        # Verificar arquivos críticos
        critical_files = ["rh_specialist.py", "telegram_agent.py", "telegram_notifier.py"]
        for file in change_request.files_to_modify:
            if file in critical_files:
                risk_factors.append(f"Modificação em arquivo crítico: {file}")
        
        # Verificar se há testes
        has_tests = any("test" in f.lower() for f in change_request.files_to_modify)
        if not has_tests and change_request.risk_level == "high":
            risk_factors.append("Alto risco sem testes")
        
        if risk_factors:
            return AgentDecision(
                agent_name=self.agent_name,
                agent_type=AgentType.REVIEW,
                decision=ApprovalStatus.REJECTED,
                reasoning=f"Riscos identificados: {', '.join(risk_factors)}",
                confidence=0.8
            )
        
        return AgentDecision(
            agent_name=self.agent_name,
            agent_type=AgentType.REVIEW,
            decision=ApprovalStatus.APPROVED,
            reasoning="Análise de bugs não identificou problemas críticos",
            confidence=0.7
        )
    
    def _review_for_security(self, change_request: ChangeRequest) -> AgentDecision:
        """Review focado em segurança"""
        security_risks = []
        
        # Verificar se há tokens/keys
        for file in change_request.files_to_modify:
            if "token" in file.lower() or "key" in file.lower() or "secret" in file.lower():
                security_risks.append(f"Modificação em arquivo de segurança: {file}")
        
        # Verificar se há network requests
        network_files = ["rh_specialist.py", "telegram_notifier.py"]
        for file in change_request.files_to_modify:
            if file in network_files:
                security_risks.append(f"Modificação em arquivo com requests: {file}")
        
        if security_risks:
            return AgentDecision(
                agent_name=self.agent_name,
                agent_type=AgentType.REVIEW,
                decision=ApprovalStatus.REJECTED,
                reasoning=f"Riscos de segurança: {', '.join(security_risks)}",
                confidence=0.9
            )
        
        return AgentDecision(
            agent_name=self.agent_name,
            agent_type=AgentType.REVIEW,
            decision=ApprovalStatus.APPROVED,
            reasoning="Análise de segurança não identificou vulnerabilidades",
            confidence=0.8
        )
    
    def _review_for_patterns(self, change_request: ChangeRequest) -> AgentDecision:
        """Review focado em padrões e convenções"""
        pattern_issues = []
        
        # Verificar convenções de Python
        for file in change_request.files_to_modify:
            if not file.endswith(".py"):
                pattern_issues.append(f"Arquivo não-Python: {file}")
        
        # Verificar se há documentação
        if change_request.risk_level == "high" and len(change_request.description) < 50:
            pattern_issues.append("Alta complexidade com pouca documentação")
        
        if pattern_issues:
            return AgentDecision(
                agent_name=self.agent_name,
                agent_type=AgentType.REVIEW,
                decision=ApprovalStatus.REJECTED,
                reasoning=f"Violações de padrão: {', '.join(pattern_issues)}",
                confidence=0.6
            )
        
        return AgentDecision(
            agent_name=self.agent_name,
            agent_type=AgentType.REVIEW,
            decision=ApprovalStatus.APPROVED,
            reasoning="Padrões e convenções seguidos corretamente",
            confidence=0.7
        )

class SkillAgentsSystem:
    """Sistema principal de agentes especialistas"""
    
    def __init__(self):
        # 2 agentes de manutenção
        self.maintenance_agents = [
            MaintenanceAgent(1),
            MaintenanceAgent(2)
        ]
        
        # 3 agentes de review
        self.review_agents = [
            ReviewAgent(1, "bugs"),
            ReviewAgent(2, "security"), 
            ReviewAgent(3, "patterns"),
            ReviewAgent(4, "stability_guard"),
        ]
    
    def request_approval(self, change_request: ChangeRequest) -> Dict[str, any]:
        """Solicita aprovação para mudança"""
        print(f"Solicitando aprovacao para: {change_request.description}")
        
        # Fase 1: Review dos 3 agentes
        print("\nFASE 1: Review dos Agentes Especialistas")
        review_decisions = []
        
        for agent in self.review_agents:
            decision = agent.analyze_change(change_request)
            review_decisions.append(decision)
            status = "[APROVADO]" if decision.decision == ApprovalStatus.APPROVED else "[REJEITADO]"
            print(f"  {status} {agent.agent_name}: {decision.reasoning}")
        
        # Verificar aprovação dos reviews
        approved_reviews = sum(1 for d in review_decisions if d.decision == ApprovalStatus.APPROVED)
        
        if approved_reviews < len(self.review_agents):
            return {
                "approved": False,
                "reason": "Rejeitado na fase de review",
                "details": review_decisions
            }
        
        # Fase 2: Verificação dos 2 agentes de manutenção
        print("\nFASE 2: Verificacao de Manutencao")
        maintenance_decisions = []
        
        for agent in self.maintenance_agents:
            decision = agent.approve_change(change_request)
            maintenance_decisions.append(decision)
            status = "[APROVADO]" if decision.decision == ApprovalStatus.APPROVED else "[REJEITADO]"
            print(f"  {status} {agent.agent_name}: {decision.reasoning}")
        
        # Verificar aprovação da manutenção
        approved_maintenance = sum(1 for d in maintenance_decisions if d.decision == ApprovalStatus.APPROVED)
        
        if approved_maintenance < 2:
            return {
                "approved": False,
                "reason": "Rejeitado na fase de manutencao",
                "details": maintenance_decisions
            }
        
        # Aprovado!
        print("\nMUDANCA APROVADA!")
        return {
            "approved": True,
            "reason": "Aprovado por todos os agentes",
            "details": {
                "review": review_decisions,
                "maintenance": maintenance_decisions
            }
        }
    
    def ask_permission_to_code(self, change_description: str, files: List[str]) -> bool:
        """Interface principal para perguntar se pode codar"""
        print(f"\nPosso codar esta alteracao?")
        print(f"Descricao: {change_description}")
        print(f"Arquivos: {', '.join(files)}")
        
        # Determinar nível de risco automaticamente
        risk_level = self._assess_risk_level(files)
        urgency = "medium"  # Default
        
        change_request = ChangeRequest(
            description=change_description,
            files_to_modify=files,
            risk_level=risk_level,
            urgency=urgency
        )
        
        # Obter aprovação dos agentes
        result = self.request_approval(change_request)
        
        if result["approved"]:
            print("Permissao concedida! Posso prosseguir com a codificacao.")
            return True
        else:
            print(f"Permissao negada! Motivo: {result['reason']}")
            return False
    
    def _assess_risk_level(self, files: List[str]) -> str:
        """Avalia nível de risco baseado nos arquivos"""
        critical_files = ["rh_specialist.py", "telegram_agent.py", "telegram_notifier.py"]
        
        if any(f in critical_files for f in files):
            return "high"
        elif len(files) > 3:
            return "medium"
        else:
            return "low"
