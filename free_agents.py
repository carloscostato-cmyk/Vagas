"""
Free Agents - Agentes Gratuitos para Reduzir Custos
Implementa agentes especializados usando LLMs gratuitos
"""

import json
import re
from typing import Dict, List, Any, Optional
from llm_optimizer import FreeAgentManager, TokenOptimizer

class FreeJobAnalyzer:
    """Analisador de vagas gratuito usando LLMs locais"""
    
    def __init__(self):
        self.agent_manager = FreeAgentManager()
        self.token_optimizer = TokenOptimizer()
    
    def analyze_job_relevance(self, title: str, description: str, candidate_profile: Dict) -> Dict[str, Any]:
        """Analisa relevância da vaga usando LLM gratuito"""
        # Otimiza prompt para economizar tokens
        prompt = f"""
        Analise vaga: {title}
        Desc: {description[:200]}...
        Perfil: {candidate_profile.get('keywords', [])[:5]}
        
        Responda JSON:
        {{
            "relevance_score": 0-100,
            "match_level": "baixo|medio|alto",
            "key_skills": ["skill1", "skill2"],
            "recommendation": "sim|nao"
        }}
        """
        
        try:
            response = self.token_optimizer.call_llm(prompt)
            # Tenta extrair JSON da resposta
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback para análise simples
        return self._simple_analysis(title, description, candidate_profile)
    
    def _simple_analysis(self, title: str, description: str, profile: Dict) -> Dict[str, Any]:
        """Análise simples sem LLM"""
        text = f"{title} {description}".lower()
        keywords = [k.lower() for k in profile.get('keywords', [])]
        
        matches = sum(1 for kw in keywords if kw in text)
        score = min(100, (matches / len(keywords)) * 100 if keywords else 0)
        
        return {
            "relevance_score": int(score),
            "match_level": "alto" if score > 70 else "medio" if score > 40 else "baixo",
            "key_skills": [kw for kw in keywords if kw in text][:3],
            "recommendation": "sim" if score > 50 else "nao"
        }

class FreeContentFilter:
    """Filtrador de conteúdo gratuito"""
    
    def __init__(self):
        self.agent_manager = FreeAgentManager()
        self.token_optimizer = TokenOptimizer()
    
    def filter_job_language(self, title: str, description: str) -> Dict[str, Any]:
        """Filtra idioma da vaga usando LLM gratuito"""
        # Análise simples de idioma sem LLM para economizar tokens
        text = f"{title} {description}".lower()
        
        portuguese_indicators = [
            "vaga", "emprego", "contratação", "salário", "benefícios",
            "gerente", "analista", "coordenador", "são paulo", "brasil"
        ]
        
        english_indicators = [
            "we are looking for", "requirements", "skills", "experience",
            "salary", "benefits", "manager", "analyst", "coordinator"
        ]
        
        pt_count = sum(1 for indicator in portuguese_indicators if indicator in text)
        en_count = sum(1 for indicator in english_indicators if indicator in text)
        
        if pt_count > en_count:
            return {"language": "portuguese", "confidence": 0.8, "recommendation": "keep"}
        elif en_count > pt_count:
            return {"language": "english", "confidence": 0.8, "recommendation": "review"}
        else:
            return {"language": "mixed", "confidence": 0.5, "recommendation": "review"}
    
    def filter_seniority_level(self, title: str, description: str) -> Dict[str, Any]:
        """Filtra nível de senioridade"""
        text = f"{title} {description}".lower()
        
        senior_indicators = ["senior", "sr.", "lead", "head", "director", "manager", "gerente"]
        junior_indicators = ["junior", "jr.", "trainee", "estágio", "intern", "entry level"]
        
        senior_count = sum(1 for indicator in senior_indicators if indicator in text)
        junior_count = sum(1 for indicator in junior_indicators if indicator in text)
        
        if senior_count > junior_count:
            return {"level": "senior", "confidence": 0.7, "recommendation": "keep"}
        elif junior_count > senior_count:
            return {"level": "junior", "confidence": 0.7, "recommendation": "filter"}
        else:
            return {"level": "mid", "confidence": 0.5, "recommendation": "review"}

class FreeJobSummarizer:
    """Resumidor de vagas gratuito"""
    
    def __init__(self):
        self.token_optimizer = TokenOptimizer()
    
    def summarize_job(self, title: str, description: str, max_length: int = 200) -> str:
        """Resume vaga usando LLM gratuito"""
        # Truncar descrição para economizar tokens
        truncated_desc = description[:500] + "..." if len(description) > 500 else description
        
        prompt = f"Resuma vaga em português (máx {max_length} chars): {title} - {truncated_desc}"
        
        try:
            summary = self.token_optimizer.call_llm(prompt)
            return summary[:max_length]
        except:
            # Fallback simples
            return f"{title}: {description[:max_length-50]}..."
    
    def extract_key_points(self, title: str, description: str) -> List[str]:
        """Extrai pontos-chave da vaga"""
        text = f"{title} {description}".lower()
        
        # Padrões comuns em vagas
        patterns = {
            "skills": r"(?:skills|competências|habilidades)[:\s]*([^.]*?)[\.\n]",
            "requirements": r"(?:requirements|requisitos)[:\s]*([^.]*?)[\.\n]",
            "benefits": r"(?:benefits|benefícios)[:\s]*([^.]*?)[\.\n]",
            "salary": r"(?:salary|salário|remuneração)[:\s]*([^.]*?)[\.\n]"
        }
        
        key_points = []
        for category, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches[:2]:  # Máximo 2 por categoria
                key_points.append(f"{category.title()}: {match.strip()}")
        
        return key_points[:5]  # Máximo 5 pontos

class FreeLocationFilter:
    """Filtrador de localização gratuito"""
    
    def __init__(self):
        self.brazilian_locations = [
            "são paulo", "rio de janeiro", "belo horizonte", "curitiba",
            "porto alegre", "recife", "fortaleza", "brasília", "salvador",
            "campinas", "guarulhos", "são bernardo do campo", "osasco",
            "santo André", "são josé dos campos", "sorocaba", "ribeirão preto",
            "natal", "joão pessoa", "teresina", "aracaju", "maceió",
            "palmas", "porto velho", "rio branco", "manaus", "boa vista"
        ]
        
        self.remote_indicators = [
            "remote", "remoto", "home office", "home-office", "trabalho remoto",
            "teletrabalho", "trabalho à distância", "work from home", "wfh"
        ]
    
    def analyze_location(self, title: str, description: str) -> Dict[str, Any]:
        """Analisa localização da vaga"""
        text = f"{title} {description}".lower()
        
        # Verifica se é remoto
        is_remote = any(indicator in text for indicator in self.remote_indicators)
        
        # Verifica localização no Brasil
        brazilian_match = None
        for location in self.brazilian_locations:
            if location in text:
                brazilian_match = location
                break
        
        # Verifica indicadores de Brasil
        brazil_indicators = ["brasil", "brazil", "brasilian", "brazilian"]
        is_brazil = any(indicator in text for indicator in brazil_indicators)
        
        if is_remote:
            return {
                "type": "remote",
                "location": "Remote",
                "is_brazil": is_brazil,
                "recommendation": "keep"
            }
        elif brazilian_match:
            return {
                "type": "onsite",
                "location": brazilian_match.title(),
                "is_brazil": True,
                "recommendation": "keep"
            }
        elif is_brazil:
            return {
                "type": "onsite",
                "location": "Brazil",
                "is_brazil": True,
                "recommendation": "keep"
            }
        else:
            return {
                "type": "international",
                "location": "International",
                "is_brazil": False,
                "recommendation": "review"
            }

class FreeAgentOrchestrator:
    """Orquestrador de agentes gratuitos"""
    
    def __init__(self):
        self.analyzer = FreeJobAnalyzer()
        self.filter = FreeContentFilter()
        self.summarizer = FreeJobSummarizer()
        self.location_filter = FreeLocationFilter()
        self.token_optimizer = TokenOptimizer()
    
    def process_job_batch(self, jobs: List[Dict], candidate_profile: Dict) -> List[Dict]:
        """Processa lote de vagas usando agentes gratuitos"""
        processed_jobs = []
        
        for job in jobs:
            try:
                processed_job = self.process_single_job(job, candidate_profile)
                if processed_job["recommendation"] == "keep":
                    processed_jobs.append(processed_job)
            except Exception as e:
                print(f"Erro processando vaga: {e}")
                continue
        
        return processed_jobs
    
    def process_single_job(self, job: Dict, candidate_profile: Dict) -> Dict:
        """Processa vaga individual"""
        title = job.get("title", "")
        description = job.get("description", "")
        
        # Análise de relevância
        relevance = self.analyzer.analyze_job_relevance(title, description, candidate_profile)
        
        # Filtros
        language_filter = self.filter.filter_job_language(title, description)
        seniority_filter = self.filter.filter_seniority_level(title, description)
        location_analysis = self.location_filter.analyze_location(title, description)
        
        # Sumarização
        summary = self.summarizer.summarize_job(title, description)
        key_points = self.summarizer.extract_key_points(title, description)
        
        # Decisão final
        recommendations = [
            language_filter["recommendation"],
            seniority_filter["recommendation"],
            location_analysis["recommendation"]
        ]
        
        final_recommendation = "keep" if recommendations.count("keep") >= 2 else "filter"
        
        return {
            "original_job": job,
            "relevance": relevance,
            "language": language_filter,
            "seniority": seniority_filter,
            "location": location_analysis,
            "summary": summary,
            "key_points": key_points,
            "recommendation": final_recommendation,
            "processing_cost": 0.0  # Gratuito
        }
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Relatório de otimização"""
        return {
            "agent_status": "active",
            "cost_per_job": 0.0,
            "savings_vs_paid_llm": "100%",
            "available_agents": [
                "FreeJobAnalyzer",
                "FreeContentFilter", 
                "FreeJobSummarizer",
                "FreeLocationFilter"
            ],
            "token_optimization": self.token_optimizer.check_provider_health()
        }

# Exemplo de uso
def demonstrate_free_agents():
    """Demonstra agentes gratuitos"""
    orchestrator = FreeAgentOrchestrator()
    
    print("=== Demonstração de Agentes Gratuitos ===")
    
    # Perfil do candidato
    candidate_profile = {
        "keywords": ["gerente de projetos", "ti", "cybersecurity", "power bi"]
    }
    
    # Vagas de exemplo
    sample_jobs = [
        {
            "title": "Gerente de TI",
            "description": "Buscamos gerente de TI com experiência em cybersecurity e Power BI para trabalhar em São Paulo."
        },
        {
            "title": "Senior Project Manager",
            "description": "We are looking for a Senior Project Manager with IT experience and cybersecurity knowledge."
        }
    ]
    
    print("\n1. Processando vagas com agentes gratuitos:")
    processed = orchestrator.process_job_batch(sample_jobs, candidate_profile)
    
    for job in processed:
        print(f"\nVaga: {job['original_job']['title']}")
        print(f"Recomendação: {job['recommendation']}")
        print(f"Resumo: {job['summary']}")
        print(f"Localização: {job['location']['type']} - {job['location']['location']}")
    
    print("\n2. Relatório de Otimização:")
    report = orchestrator.get_optimization_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    demonstrate_free_agents()
