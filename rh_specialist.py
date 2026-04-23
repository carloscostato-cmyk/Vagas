"""
RH Specialist Agent — Busca real de vagas + notificação Telegram.
Busca vagas em fontes públicas e envia relatório ao Carlos via bot.
"""

import os
import json
import requests
from datetime import datetime
from telegram_notifier import TelegramNotifier


# --------------------------------------------------------------------------- #
# Configuração do Perfil do Candidato
# --------------------------------------------------------------------------- #
CANDIDATE = {
    "name": "Carlos Costato",
    "keywords": [
        "Senior IT Project Manager",
        "Gerente de Projetos",
        "Head of IT",
        "IT Director",
        "Gerente de TI",
        "Cybersecurity Manager",
        "Information Security Manager",
        "AI Project Manager",
        "Gerente de Inteligência Artificial",
        "Technology Manager",
        "Digital Transformation Lead",
        "Scrum Master Sênior",
        "Agile Coach",
    ],
    "locations": ["São Paulo", "Remote", "Remoto", "Brasil", "Híbrido", "Hybrid"],
    "score_keywords": [
        # Hard Skills Core
        "IA", "AI", "Artificial Intelligence", "Inteligência Artificial", "Generative AI",
        "Cybersecurity", "Cibersegurança", "InfoSec", "Information Security",
        "Governance", "Governança", "Compliance", "Risk Management", "Gestão de Riscos",
        
        # Cargo e Senioridade
        "Senior", "Sênior", "Project Manager", "Gestor de Projetos", "Liderança", 
        "Leadership", "Head", "Manager", "Gerente", "Enterprise", "Missão Crítica",
        
        # Tecnologias e Ferramentas
        "Power Platform", "Power BI", "Power Automate", "Power Apps", "SharePoint", 
        "Microsoft 365", "RPA", "Automação", "Automation", "Dashboard", "BI", 
        "Business Intelligence", "Analytics",
        
        # Metodologias
        "Transformação Digital", "Digital Transformation", "Agile", "Ágil", "Scrum", 
        "Kanban", "ITIL", "COBIT", "PMBOK", "SLA", "KPI", "ROI",
        
        # Diferenciais Pessoais
        "FIAP", "Inglês", "Estratégia", "Strategy", "Inovação", "Innovation"
    ],
}

APPLICATIONS_FILE = os.path.join(os.path.dirname(__file__), "applications.json")


# --------------------------------------------------------------------------- #
# Funções de Busca (fontes públicas via RSS / APIs abertas)
# --------------------------------------------------------------------------- #

def fetch_remotive_jobs() -> list:
    """Busca vagas via API pública do Remotive.io (sem autenticação)."""
    jobs_found = []
    search_terms = ["project manager", "IT manager", "cybersecurity", "AI manager", "digital transformation", "scrum master", "IT governance"]
    try:
        for kw in search_terms:
            url = f"https://remotive.com/api/remote-jobs?search={kw.replace(' ', '+')}&limit=10"
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for job in data.get("jobs", []):
                    jobs_found.append({
                        "title": job.get("title", ""),
                        "company": job.get("company_name", ""),
                        "url": job.get("url", ""),
                        "description": job.get("description", ""),
                        "source": "Remotive",
                        "found_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })
    except Exception as e:
        print(f"⚠️  Remotive fetch error: {e}")
    return jobs_found


def fetch_arbeitnow_jobs() -> list:
    """Busca vagas via API pública do Arbeitnow (sem autenticação)."""
    jobs_found = []
    try:
        url = "https://www.arbeitnow.com/api/job-board-api?search=IT+project+manager"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            for job in data.get("data", []):
                jobs_found.append({
                    "title": job.get("title", ""),
                    "company": job.get("company_name", ""),
                    "url": job.get("url", ""),
                    "description": job.get("description", ""),
                    "source": "Arbeitnow",
                    "found_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
    except Exception as e:
        print(f"⚠️  Arbeitnow fetch error: {e}")
    return jobs_found


# --------------------------------------------------------------------------- #
# Motor de Pontuação
# --------------------------------------------------------------------------- #

def calculate_match(title: str, description: str) -> int:
    """Pontua a aderência da vaga ao perfil do Carlos."""
    score = 0
    text = f"{title} {description}".lower()
    
    # Bonificação por palavra encontrada (max 100)
    for kw in CANDIDATE["score_keywords"]:
        if kw.lower() in text:
            # Palavras essenciais valem mais
            if kw.lower() in ["senior", "sênior", "project manager", "cybersecurity", "ia", "ai", "governança", "governance", "head"]:
                score += 15
            else:
                score += 8
                
    return min(score, 100)

def filter_and_score(raw_jobs: list) -> list:
    """Filtra e pontua vagas, retornando apenas as relevantes."""
    scored = []
    for job in raw_jobs:
        # Descartar sumariamente vagas sem link válido
        url = job.get("url", "")
        if not url or url == "#" or not url.startswith("http"):
            continue
            
        score = calculate_match(job["title"], job.get("description", ""))
        if score >= 40:  # Match mínimo aceitável (equivale a umas 3-4 keywords fortes)
            job["match_score"] = score
            scored.append(job)
    # Ordena do maior match para o menor
    return sorted(scored, key=lambda x: x["match_score"], reverse=True)


# --------------------------------------------------------------------------- #
# Persistência no applications.json
# --------------------------------------------------------------------------- #

def load_existing_applications() -> list:
    try:
        with open(APPLICATIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_applications(apps: list):
    with open(APPLICATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(apps, f, indent=4, ensure_ascii=False)


def deduplicate_and_save(new_jobs: list) -> list:
    """Salva apenas vagas novas (evita duplicatas por URL)."""
    existing = load_existing_applications()
    existing_urls = {app.get("url") for app in existing}
    truly_new = [j for j in new_jobs if j.get("url") not in existing_urls]
    if truly_new:
        save_applications(existing + truly_new)
        print(f"💾 {len(truly_new)} nova(s) vaga(s) salva(s) em applications.json")
    else:
        print("ℹ️  Nenhuma vaga nova para salvar.")
    return truly_new


# --------------------------------------------------------------------------- #
# Ponto de Entrada Principal
# --------------------------------------------------------------------------- #

def run_agent(session_label: str = "Ciclo Automático"):
    print(f"\n{'='*60}")
    print(f"🤖 AGENTE DE RH INICIADO — {session_label}")
    print(f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} (UTC)")
    print(f"{'='*60}\n")

    notifier = TelegramNotifier()

    try:
        print("🔍 Buscando vagas nas fontes públicas...")
        raw_jobs = []
        raw_jobs += fetch_remotive_jobs()
        raw_jobs += fetch_arbeitnow_jobs()
        print(f"   → {len(raw_jobs)} vagas brutas coletadas.")

        print("📊 Filtrando e pontuando vagas para o perfil do Carlos...")
        matched_jobs = filter_and_score(raw_jobs)
        print(f"   → {len(matched_jobs)} vagas com match suficiente.")

        new_jobs = deduplicate_and_save(matched_jobs)
        print(f"   → {len(new_jobs)} são novas (não vistas antes).")

        print("\n📨 Enviando relatório ao Telegram...")
        notifier.send_job_report(
            jobs=new_jobs if new_jobs else matched_jobs[:5],
            session_label=session_label,
        )

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        notifier.send_error_alert(str(e))
        raise


if __name__ == "__main__":
    import sys
    label = sys.argv[1] if len(sys.argv) > 1 else "Manual"
    run_agent(session_label=label)
