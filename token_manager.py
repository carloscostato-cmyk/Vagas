"""
Token Manager - Gerenciador Inteligente de Tokens
Controla uso de tokens e alterna entre provedores gratuitos/pagos
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

class TokenPriority(Enum):
    FREE = 1
    LOW_COST = 2
    STANDARD = 3
    PREMIUM = 4

@dataclass
class TokenUsage:
    timestamp: datetime
    provider: str
    tokens_used: int
    cost: float
    priority: TokenPriority

@dataclass
class ProviderConfig:
    name: str
    endpoint: str
    cost_per_1k_tokens: float
    max_tokens_per_request: int
    rate_limit_per_minute: int
    priority: TokenPriority
    is_available: bool = True

class TokenManager:
    """Gerenciador inteligente de tokens para economia"""
    
    def __init__(self):
        self.providers = self._setup_providers()
        self.usage_history: List[TokenUsage] = []
        self.daily_budget = 10.0  # $10 por dia
        self.monthly_budget = 200.0  # $200 por mês
        self.current_usage = 0.0
        self.last_reset = datetime.now().date()
    
    def _setup_providers(self) -> Dict[str, ProviderConfig]:
        """Configura provedores com prioridades"""
        return {
            "ollama": ProviderConfig(
                name="Ollama Local",
                endpoint="http://localhost:11434",
                cost_per_1k_tokens=0.0,  # Gratuito
                max_tokens_per_request=4000,
                rate_limit_per_minute=60,
                priority=TokenPriority.FREE
            ),
            "lm_studio": ProviderConfig(
                name="LM Studio Local",
                endpoint="http://localhost:1234",
                cost_per_1k_tokens=0.0,  # Gratuito
                max_tokens_per_request=4000,
                rate_limit_per_minute=60,
                priority=TokenPriority.FREE
            ),
            "groq": ProviderConfig(
                name="Groq",
                endpoint="https://api.groq.com",
                cost_per_1k_tokens=0.001,  # $0.001 por 1K
                max_tokens_per_request=8000,
                rate_limit_per_minute=30,
                priority=TokenPriority.LOW_COST
            ),
            "huggingface": ProviderConfig(
                name="HuggingFace Inference",
                endpoint="https://api-inference.huggingface.co",
                cost_per_1k_tokens=0.002,  # $0.002 por 1K
                max_tokens_per_request=4000,
                rate_limit_per_minute=20,
                priority=TokenPriority.LOW_COST
            ),
            "openai": ProviderConfig(
                name="OpenAI GPT",
                endpoint="https://api.openai.com",
                cost_per_1k_tokens=0.02,  # $0.02 por 1K
                max_tokens_per_request=4000,
                rate_limit_per_minute=60,
                priority=TokenPriority.STANDARD
            ),
            "claude": ProviderConfig(
                name="Claude",
                endpoint="https://api.anthropic.com",
                cost_per_1k_tokens=0.015,  # $0.015 por 1K
                max_tokens_per_request=4000,
                rate_limit_per_minute=50,
                priority=TokenPriority.STANDARD
            )
        }
    
    def get_best_provider(self, estimated_tokens: int) -> Optional[str]:
        """Seleciona melhor provedor baseado em custo e disponibilidade"""
        # Reset diário se necessário
        if datetime.now().date() > self.last_reset:
            self._reset_daily_usage()
        
        # Filtra provedores disponíveis
        available_providers = {
            name: config for name, config in self.providers.items()
            if config.is_available and config.max_tokens_per_request >= estimated_tokens
        }
        
        # Ordena por prioridade (custo mais baixo primeiro)
        sorted_providers = sorted(
            available_providers.items(),
            key=lambda x: (x[1].priority.value, x[1].cost_per_1k_tokens)
        )
        
        # Verifica orçamento
        for name, config in sorted_providers:
            estimated_cost = (estimated_tokens / 1000) * config.cost_per_1k_tokens
            
            if self._can_afford(estimated_cost):
                return name
        
        return None  # Nenhum provedor disponível dentro do orçamento
    
    def _can_afford(self, cost: float) -> bool:
        """Verifica se pode custear o uso"""
        daily_remaining = self.daily_budget - self.current_usage
        return cost <= daily_remaining
    
    def _reset_daily_usage(self):
        """Reseta uso diário"""
        self.current_usage = 0.0
        self.last_reset = datetime.now().date()
        print("Uso diário de tokens resetado")
    
    def record_usage(self, provider: str, tokens_used: int):
        """Registra uso de tokens"""
        if provider not in self.providers:
            return
        
        config = self.providers[provider]
        cost = (tokens_used / 1000) * config.cost_per_1k_tokens
        
        usage = TokenUsage(
            timestamp=datetime.now(),
            provider=provider,
            tokens_used=tokens_used,
            cost=cost,
            priority=config.priority
        )
        
        self.usage_history.append(usage)
        self.current_usage += cost
        
        # Remove registros antigos (mantém 30 dias)
        cutoff_date = datetime.now() - timedelta(days=30)
        self.usage_history = [
            u for u in self.usage_history 
            if u.timestamp > cutoff_date
        ]
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso"""
        if not self.usage_history:
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "daily_usage": self.current_usage,
                "daily_budget": self.daily_budget,
                "provider_breakdown": {}
            }
        
        total_tokens = sum(u.tokens_used for u in self.usage_history)
        total_cost = sum(u.cost for u in self.usage_history)
        
        provider_breakdown = {}
        for usage in self.usage_history:
            if usage.provider not in provider_breakdown:
                provider_breakdown[usage.provider] = {
                    "tokens": 0,
                    "cost": 0.0,
                    "requests": 0
                }
            provider_breakdown[usage.provider]["tokens"] += usage.tokens_used
            provider_breakdown[usage.provider]["cost"] += usage.cost
            provider_breakdown[usage.provider]["requests"] += 1
        
        return {
            "total_requests": len(self.usage_history),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "daily_usage": self.current_usage,
            "daily_budget": self.daily_budget,
            "daily_remaining": self.daily_budget - self.current_usage,
            "provider_breakdown": provider_breakdown
        }
    
    def get_cost_optimization_tips(self) -> List[str]:
        """Retorna dicas de otimização de custos"""
        tips = []
        stats = self.get_usage_stats()
        
        # Verifica uso de provedores pagos vs gratuitos
        free_usage = 0
        paid_usage = 0
        
        for provider, data in stats["provider_breakdown"].items():
            if self.providers[provider].priority == TokenPriority.FREE:
                free_usage += data["cost"]
            else:
                paid_usage += data["cost"]
        
        if paid_usage > free_usage * 2:
            tips.append("Considere usar mais provedores gratuitos como Ollama ou LM Studio")
        
        # Verifica uso diário
        if stats["daily_usage"] > stats["daily_budget"] * 0.8:
            tips.append("Você está próximo do limite diário. Considere otimizar prompts.")
        
        # Verifica eficiência
        if stats["total_requests"] > 0:
            avg_tokens_per_request = stats["total_tokens"] / stats["total_requests"]
            if avg_tokens_per_request > 1000:
                tips.append("Considere reduzir o tamanho dos prompts para economizar tokens")
        
        # Verifica provedor mais usado
        most_used_provider = max(
            stats["provider_breakdown"].items(),
            key=lambda x: x[1]["requests"]
        )[0]
        
        if self.providers[most_used_provider].priority != TokenPriority.FREE:
            tips.append(f"O provedor mais usado ({most_used_provider}) não é gratuito. Considere alternativas.")
        
        return tips
    
    def estimate_monthly_savings(self) -> Dict[str, Any]:
        """Estima economia mensal com otimização"""
        stats = self.get_usage_stats()
        
        # Simula uso 100% gratuito
        current_month_cost = stats["total_cost"]
        projected_monthly = current_month_cost * 30  # Projeção simples
        
        # Calcula economia potencial com provedores gratuitos
        free_provider_usage = 0
        for provider, data in stats["provider_breakdown"].items():
            if self.providers[provider].priority == TokenPriority.FREE:
                free_provider_usage += data["tokens"]
        
        # Se 100% gratuito
        if stats["total_tokens"] > 0:
            free_ratio = free_provider_usage / stats["total_tokens"]
            potential_savings = current_month_cost * (1 - free_ratio)
        else:
            potential_savings = 0
        
        return {
            "current_monthly_projection": projected_monthly,
            "potential_monthly_savings": potential_savings,
            "free_provider_usage_percentage": free_ratio * 100 if stats["total_tokens"] > 0 else 0,
            "optimization_tips": self.get_cost_optimization_tips()
        }
    
    def set_budget(self, daily: float = None, monthly: float = None):
        """Ajusta limites de orçamento"""
        if daily is not None:
            self.daily_budget = daily
        if monthly is not None:
            self.monthly_budget = monthly
        
        print(f"Orçamento atualizado: Diário=${self.daily_budget}, Mensal=${self.monthly_budget}")
    
    def export_usage_report(self, filename: str = None) -> str:
        """Exporta relatório de uso"""
        if filename is None:
            filename = f"token_usage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "usage_stats": self.get_usage_stats(),
            "monthly_savings": self.estimate_monthly_savings(),
            "providers": {name: asdict(config) for name, config in self.providers.items()}
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        return filename

# Exemplo de uso
def demonstrate_token_management():
    """Demonstra gerenciamento de tokens"""
    manager = TokenManager()
    
    print("=== Demonstração de Gerenciamento de Tokens ===")
    
    # Simula uso
    manager.record_usage("ollama", 500)
    manager.record_usage("openai", 1000)
    manager.record_usage("groq", 300)
    
    print("\n1. Estatísticas de Uso:")
    stats = manager.get_usage_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    print("\n2. Melhor Provedor para 1000 tokens:")
    best_provider = manager.get_best_provider(1000)
    print(f"Melhor provedor: {best_provider}")
    
    print("\n3. Dicas de Otimização:")
    tips = manager.get_cost_optimization_tips()
    for tip in tips:
        print(f"- {tip}")
    
    print("\n4. Economia Mensal Estimada:")
    savings = manager.estimate_monthly_savings()
    print(json.dumps(savings, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    demonstrate_token_management()
