from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Recommendation:
    title: str
    reason: str
    confidence: float


def _has_any(text: str, keywords: list[str]) -> bool:
    t = text.lower()
    return any(k in t for k in keywords)


def recommend_from_text(text: str, limit: int = 8) -> list[Recommendation]:
    """
    MVP heurístico (local): gera sugestões iniciais sem depender de LLM.
    Depois a gente troca por “agentes”/LLM mantendo a mesma interface.
    """
    t = re.sub(r"\s+", " ", (text or "").strip())
    if not t:
        return [
            Recommendation(
                title="Preencha ou envie um currículo",
                reason="Não encontrei texto suficiente para analisar. Envie PDF/DOCX/TXT.",
                confidence=0.1,
            )
        ]

    recs: list[Recommendation] = []

    if _has_any(t, ["python", "django", "flask", "fastapi", "api", "backend", "sql", "postgres", "mysql"]):
        recs.append(
            Recommendation(
                title="Desenvolvedor(a) Backend",
                reason="Experiência/termos típicos de APIs, banco de dados e backend.",
                confidence=0.75,
            )
        )

    if _has_any(t, ["react", "typescript", "javascript", "frontend", "css", "html", "next.js", "vue"]):
        recs.append(
            Recommendation(
                title="Desenvolvedor(a) Frontend",
                reason="Termos fortes de front-end (JS/TS, frameworks e UI).",
                confidence=0.72,
            )
        )

    if _has_any(t, ["aws", "azure", "gcp", "docker", "kubernetes", "devops", "terraform", "ci/cd", "ci cd"]):
        recs.append(
            Recommendation(
                title="DevOps / Plataforma",
                reason="Sinais de cloud, containers, infraestrutura como código e automação.",
                confidence=0.74,
            )
        )

    if _has_any(t, ["scrum", "kanban", "stakeholder", "roadmap", "prazo", "escopo", "pmo", "pmp", "gerente de projetos"]):
        recs.append(
            Recommendation(
                title="Gerente de Projetos (TI)",
                reason="Linguagem e termos de gestão de projetos e governança.",
                confidence=0.7,
            )
        )

    if _has_any(t, ["power bi", "tableau", "sql", "etl", "dash", "dashboard", "analytics", "bi", "data"]):
        recs.append(
            Recommendation(
                title="Analista de Dados / BI",
                reason="Sinais de BI/analytics, dashboards, modelagem e dados.",
                confidence=0.68,
            )
        )

    if _has_any(t, ["qa", "teste", "testes", "cypress", "selenium", "pytest", "automação de testes"]):
        recs.append(
            Recommendation(
                title="QA / Analista de Testes",
                reason="Experiência explícita com testes e/ou automação.",
                confidence=0.7,
            )
        )

    if _has_any(t, ["suporte", "atendimento", "customer success", "cs", "help desk", "itil"]):
        recs.append(
            Recommendation(
                title="Customer Success / Suporte",
                reason="Sinais de atendimento, suporte e rotinas de sucesso do cliente.",
                confidence=0.62,
            )
        )

    if not recs:
        recs.append(
            Recommendation(
                title="Assistente Administrativo(a) / Operações",
                reason="Não encontrei sinais fortes de uma trilha específica; posso refinar com mais detalhes.",
                confidence=0.35,
            )
        )

    recs = sorted(recs, key=lambda r: r.confidence, reverse=True)
    return recs[: max(1, min(20, limit))]

