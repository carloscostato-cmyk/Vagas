"""
LLM Optimizer - Sistema de Economia de Tokens com LLMs Gratuitos
Implementa múltiplos agentes gratuitos para reduzir custos
"""

import json
import requests
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class LLMProvider(Enum):
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio" 
    OPENAI_COMPATIBLE = "openai_compatible"
    LOCAL_LLAMA = "local_llama"
    FREE_API = "free_api"

@dataclass
class LLMConfig:
    provider: LLMProvider
    endpoint: str
    model: str
    api_key: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    free_tier: bool = True

class TokenOptimizer:
    """Otimizador de tokens com múltiplos LLMs gratuitos"""
    
    def __init__(self):
        self.providers = self._setup_free_providers()
        self.current_provider = 0
        self.usage_stats = {
            "total_requests": 0,
            "tokens_saved": 0,
            "cost_savings": 0.0
        }
    
    def _setup_free_providers(self) -> List[LLMConfig]:
        """Configura provedores gratuitos de LLM"""
        providers = []
        
        # Ollama (local gratuito)
        providers.append(LLMConfig(
            provider=LLMProvider.OLLAMA,
            endpoint="http://localhost:11434",
            model="llama3.2:3b",
            max_tokens=4000,
            free_tier=True
        ))
        
        # LM Studio (local gratuito)
        providers.append(LLMConfig(
            provider=LLMProvider.LM_STUDIO,
            endpoint="http://localhost:1234",
            model="local-model",
            max_tokens=4000,
            free_tier=True
        ))
        
        # Groq (gratuito até certo limite)
        providers.append(LLMConfig(
            provider=LLMProvider.OPENAI_COMPATIBLE,
            endpoint="https://api.groq.com/openai/v1",
            model="llama-3.1-8b-instant",
            api_key="gsk_...",  # Precisa configurar
            max_tokens=4000,
            free_tier=True
        ))
        
        # HuggingFace Inference API (gratuito)
        providers.append(LLMConfig(
            provider=LLMProvider.OPENAI_COMPATIBLE,
            endpoint="https://api-inference.huggingface.co",
            model="microsoft/DialoGPT-medium",
            api_key="hf_...",  # Precisa configurar
            max_tokens=4000,
            free_tier=True
        ))
        
        return providers
    
    def optimize_prompt(self, prompt: str, max_length: int = 1000) -> str:
        """Otimiza prompt para economizar tokens"""
        # Remove redundância
        prompt = self._remove_redundancy(prompt)
        
        # Usa abreviações inteligentes
        prompt = self._use_abbreviations(prompt)
        
        # Limita tamanho
        if len(prompt) > max_length:
            prompt = prompt[:max_length] + "..."
        
        return prompt
    
    def _remove_redundancy(self, text: str) -> str:
        """Remove redundância do texto"""
        # Remove palavras repetidas
        words = text.split()
        filtered_words = []
        prev_word = ""
        
        for word in words:
            if word.lower() != prev_word.lower():
                filtered_words.append(word)
            prev_word = word
        
        return " ".join(filtered_words)
    
    def _use_abbreviations(self, text: str) -> str:
        """Usa abreviações para economizar tokens"""
        abbreviations = {
            "por exemplo": "ex:",
            "ou seja": "ie:",
            "portanto": "logo",
            "entretanto": "mas",
            "consequentemente": "logo",
            "adicionamente": "tb",
            "gerenciamento": "mgmt",
            "desenvolvimento": "dev",
            "tecnologia": "tech",
            "análise": "anál",
            "implementação": "impl",
            "otimização": "opt",
        }
        
        for full, abbr in abbreviations.items():
            text = text.replace(full, abbr)
        
        return text
    
    def call_llm(self, prompt: str, provider_index: Optional[int] = None) -> str:
        """Chama LLM com rotação automática para economia"""
        if provider_index is None:
            provider_index = self.current_provider
            self.current_provider = (self.current_provider + 1) % len(self.providers)
        
        provider = self.providers[provider_index]
        
        try:
            if provider.provider == LLMProvider.OLLAMA:
                return self._call_ollama(prompt, provider)
            elif provider.provider == LLMProvider.LM_STUDIO:
                return self._call_lm_studio(prompt, provider)
            else:
                return self._call_openai_compatible(prompt, provider)
        except Exception as e:
            print(f"Erro com provedor {provider.provider}: {e}")
            # Tenta próximo provedor
            return self.call_llm(prompt, (provider_index + 1) % len(self.providers))
    
    def _call_ollama(self, prompt: str, config: LLMConfig) -> str:
        """Chama Ollama local"""
        response = requests.post(
            f"{config.endpoint}/api/generate",
            json={
                "model": config.model,
                "prompt": self.optimize_prompt(prompt),
                "stream": False
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("response", "")
    
    def _call_lm_studio(self, prompt: str, config: LLMConfig) -> str:
        """Chama LM Studio local"""
        response = requests.post(
            f"{config.endpoint}/v1/chat/completions",
            json={
                "model": config.model,
                "messages": [{"role": "user", "content": self.optimize_prompt(prompt)}],
                "max_tokens": config.max_tokens,
                "temperature": config.temperature
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def _call_openai_compatible(self, prompt: str, config: LLMConfig) -> str:
        """Chama API compatível com OpenAI"""
        headers = {}
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"
        
        response = requests.post(
            f"{config.endpoint}/chat/completions",
            json={
                "model": config.model,
                "messages": [{"role": "user", "content": self.optimize_prompt(prompt)}],
                "max_tokens": config.max_tokens,
                "temperature": config.temperature
            },
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def check_provider_health(self) -> Dict[str, bool]:
        """Verifica saúde dos provedores"""
        health_status = {}
        
        for i, provider in enumerate(self.providers):
            try:
                if provider.provider == LLMProvider.OLLAMA:
                    response = requests.get(f"{provider.endpoint}/api/tags", timeout=5)
                    health_status[provider.provider.value] = response.status_code == 200
                elif provider.provider == LLMProvider.LM_STUDIO:
                    response = requests.get(f"{provider.endpoint}/v1/models", timeout=5)
                    health_status[provider.provider.value] = response.status_code == 200
                else:
                    health_status[provider.provider.value] = True  # Assume online
            except:
                health_status[provider.provider.value] = False
        
        return health_status
    
    def estimate_savings(self) -> Dict[str, Any]:
        """Estima economia de tokens e custos"""
        # Assume $0.01 por 1K tokens para LLMs pagos
        cost_per_1k_tokens = 0.01
        
        estimated_tokens_saved = self.usage_stats["total_requests"] * 500  # Média 500 tokens por request
        estimated_cost_savings = (estimated_tokens_saved / 1000) * cost_per_1k_tokens
        
        return {
            "tokens_saved": estimated_tokens_saved,
            "cost_savings": estimated_cost_savings,
            "free_providers_used": len([p for p in self.providers if p.free_tier]),
            "total_requests": self.usage_stats["total_requests"]
        }

class FreeAgentManager:
    """Gerenciador de agentes gratuitos"""
    
    def __init__(self):
        self.token_optimizer = TokenOptimizer()
        self.agents = self._setup_free_agents()
    
    def _setup_free_agents(self) -> Dict[str, Any]:
        """Configura agentes gratuitos"""
        return {
            "summarizer": self._create_summarizer_agent(),
            "translator": self._create_translator_agent(),
            "analyzer": self._create_analyzer_agent(),
            "filter": self._create_filter_agent(),
            "formatter": self._create_formatter_agent()
        }
    
    def _create_summarizer_agent(self):
        """Agente resumidor gratuito"""
        def summarize(text: str) -> str:
            prompt = f"Resuma em português: {text}"
            return self.token_optimizer.call_llm(prompt)
        return summarize
    
    def _create_translator_agent(self):
        """Agente tradutor gratuito"""
        def translate(text: str, target_lang: str = "pt") -> str:
            prompt = f"Traduza para {target_lang}: {text}"
            return self.token_optimizer.call_llm(prompt)
        return translate
    
    def _create_analyzer_agent(self):
        """Agente analisador gratuito"""
        def analyze(text: str) -> str:
            prompt = f"Analise este texto: {text}"
            return self.token_optimizer.call_llm(prompt)
        return analyze
    
    def _create_filter_agent(self):
        """Agente filtrador gratuito"""
        def filter_content(text: str, criteria: str) -> str:
            prompt = f"Filtre conteúdo baseado em '{criteria}': {text}"
            return self.token_optimizer.call_llm(prompt)
        return filter_content
    
    def _create_formatter_agent(self):
        """Agente formatador gratuito"""
        def format_text(text: str, format_type: str) -> str:
            prompt = f"Formate como {format_type}: {text}"
            return self.token_optimizer.call_llm(prompt)
        return format_text
    
    def run_agent(self, agent_name: str, *args, **kwargs) -> str:
        """Executa agente específico"""
        if agent_name in self.agents:
            return self.agents[agent_name](*args, **kwargs)
        else:
            raise ValueError(f"Agente '{agent_name}' não encontrado")
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Relatório de otimização"""
        health = self.token_optimizer.check_provider_health()
        savings = self.token_optimizer.estimate_savings()
        
        return {
            "provider_health": health,
            "estimated_savings": savings,
            "available_agents": list(self.agents.keys()),
            "total_providers": len(self.token_optimizer.providers)
        }

# Exemplo de uso
def demonstrate_token_optimization():
    """Demonstra economia de tokens"""
    manager = FreeAgentManager()
    
    print("=== Demonstração de Economia de Tokens ===")
    
    # Testa agentes
    test_text = "Este é um texto longo para testar a economia de tokens com múltiplos LLMs gratuitos."
    
    print("\n1. Testando Agente Resumidor:")
    summary = manager.run_agent("summarizer", test_text)
    print(f"Resumo: {summary}")
    
    print("\n2. Testando Agente Analisador:")
    analysis = manager.run_agent("analyzer", test_text)
    print(f"Análise: {analysis}")
    
    print("\n3. Relatório de Otimização:")
    report = manager.get_optimization_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    demonstrate_token_optimization()
