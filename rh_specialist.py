"""
RH Specialist Agent — Busca real de vagas + notificação Telegram.
Busca vagas em fontes públicas e envia relatório ao Carlos via bot.
"""

import os
import json
import requests
from datetime import datetime
from urllib.parse import quote_plus, urlparse
from bs4 import BeautifulSoup
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
        "FIAP", "Estratégia", "Strategy", "Inovação", "Innovation"
    ],
}


# Política de idioma do perfil:
# - Permitido: inglês técnico/intermediário
# - Bloqueado: inglês avançado/fluente obrigatório
DISALLOWED_LANGUAGE_PATTERNS = [
    "fluent english required",
    "advanced english required",
    "business fluent english",
    "professional english required",
    "native english",
    "english is mandatory",
    "mandatory english",
    "c1 english",
    "c2 english",
    "english proficiency c1",
    "english proficiency c2",
    "bilingual mandatory",
    "must be fluent in english",
    "inglês fluente obrigatório",
    "ingles fluente obrigatorio",
    "inglês avançado obrigatório",
    "ingles avancado obrigatorio",
    "inglês obrigatório",
    "ingles obrigatorio",
]
APPLICATIONS_FILE = os.path.join(os.path.dirname(__file__), "applications.json")
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


# --------------------------------------------------------------------------- #
# Funções de Busca (fontes públicas via RSS / APIs abertas)
# --------------------------------------------------------------------------- #

def fetch_remotive_jobs() -> list:
    """Busca vagas via API pública do Remotive.io (sem autenticação)."""
    jobs_found = []
    search_terms = [
        "project manager", "IT manager", "cybersecurity", "AI manager",
        "digital transformation", "scrum master", "IT governance",
        "gerente de projetos", "gerente de ti", "inteligencia artificial",
        "freelance project manager", "contract it manager"
    ]
    try:
        for kw in search_terms:
            url = f"https://remotive.com/api/remote-jobs?search={quote_plus(kw)}&limit=12"
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
                        "location": job.get("candidate_required_location", "Remote"),
                        "found_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })
    except Exception as e:
        print(f"⚠️  Remotive fetch error: {e}")
    return jobs_found


def fetch_arbeitnow_jobs() -> list:
    """Busca vagas via API pública do Arbeitnow (sem autenticação)."""
    jobs_found = []
    try:
        searches = ["IT+project+manager", "cybersecurity", "digital+transformation", "scrum+master"]
        for term in searches:
            url = f"https://www.arbeitnow.com/api/job-board-api?search={term}"
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
                        "location": job.get("location", "Remote"),
                        "found_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })
    except Exception as e:
        print(f"⚠️  Arbeitnow fetch error: {e}")
    return jobs_found


def fetch_linkedin_jobs() -> list:
    """Busca vagas públicas via endpoint guest do LinkedIn (sem autenticação)."""
    jobs_found = []
    keywords = [
        "Senior IT Project Manager",
        "Gerente de Projetos",
        "Cybersecurity Manager",
        "Head of IT",
        "AI Project Manager",
    ]

    try:
        for kw in keywords:
            url = (
                "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
                f"?keywords={quote_plus(kw)}&location={quote_plus('Brasil')}&start=0"
            )
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=20)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            for card in soup.select("li"):
                title_el = card.select_one("h3.base-search-card__title")
                company_el = card.select_one("h4.base-search-card__subtitle")
                link_el = card.select_one("a.base-card__full-link")
                location_el = card.select_one("span.job-search-card__location")

                title = title_el.get_text(" ", strip=True) if title_el else ""
                company = company_el.get_text(" ", strip=True) if company_el else ""
                job_url = link_el.get("href", "").strip() if link_el else ""
                location = location_el.get_text(" ", strip=True) if location_el else "Brasil"
                description = f"{title} {company} {location}"

                if title and job_url:
                    jobs_found.append({
                        "title": title,
                        "company": company,
                        "url": job_url,
                        "description": description,
                        "source": "LinkedIn",
                        "location": location,
                        "found_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })
    except Exception as e:
        print(f"⚠️  LinkedIn fetch error: {e}")

    return jobs_found


def fetch_remoteok_freelance_jobs() -> list:
    """Busca vagas freelance/contract via API pública do RemoteOK."""
    jobs_found = []
    try:
        resp = requests.get("https://remoteok.com/api", headers=REQUEST_HEADERS, timeout=20)
        if resp.status_code != 200:
            return jobs_found

        data = resp.json()
        for job in data:
            if not isinstance(job, dict):
                continue

            title = job.get("position", "")
            company = job.get("company", "")
            tags = " ".join(job.get("tags", []))
            desc = f"{job.get('description', '')} {tags}".lower()
            url = job.get("url", "")
            if url.startswith("/"):
                url = f"https://remoteok.com{url}"

            is_freelance = any(t in desc for t in ["freelance", "contract", "consult", "consultant"])
            if not is_freelance:
                continue

            jobs_found.append({
                "title": title,
                "company": company,
                "url": url,
                "description": f"{job.get('description', '')} {tags}",
                "source": "Freelance",
                "location": job.get("location", "Remote"),
                "found_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
    except Exception as e:
        print(f"⚠️  RemoteOK fetch error: {e}")

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
    def is_language_requirement_compatible(job: dict) -> bool:
        """Filtra vagas incompatíveis com o nível de inglês definido no perfil."""
        text = " ".join([
            str(job.get("title", "")),
            str(job.get("description", "")),
            str(job.get("requirements", "")),
        ]).lower()
        return not any(pattern in text for pattern in DISALLOWED_LANGUAGE_PATTERNS)
                
    return min(score, 100)


def is_profile_related(title: str, description: str) -> bool:
    """Garante aderência mínima da vaga ao perfil-alvo."""
    text = f"{title} {description}".lower()
    return any(kw.lower() in text for kw in CANDIDATE["keywords"]) or any(
        kw.lower() in text for kw in ["project manager", "gerente", "it", "cyber", "security", "ai", "transforma"]
    )


def is_valid_job_url(url: str) -> bool:
    """Valida formato básico de URL para evitar links inválidos no dashboard."""
            if not is_language_requirement_compatible(job):
                continue
    if not url or url in ("#", ""):
        return False
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False

def filter_and_score(raw_jobs: list) -> list:
    """Filtra e pontua vagas, retornando apenas as relevantes."""
    scored = []
    for job in raw_jobs:
        # Descartar sumariamente vagas sem link válido
        url = job.get("url", "")
        if not is_valid_job_url(url):
            continue

        title = job.get("title", "")
        description = job.get("description", "")
        if not is_profile_related(title, description):
            continue
            
        score = calculate_match(title, description)
        if score >= 30:  # Match mínimo adaptado para fontes com descrição curta
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
    existing = [
        app for app in load_existing_applications()
        if is_valid_job_url(app.get("url", "")) and is_language_requirement_compatible(app)
    ]
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
        raw_jobs += fetch_linkedin_jobs()
        raw_jobs += fetch_remoteok_freelance_jobs()
        print(f"   → {len(raw_jobs)} vagas brutas coletadas.")

        print("📊 Filtrando e pontuando vagas para o perfil do Carlos...")
        matched_jobs = filter_and_score(raw_jobs)
        print(f"   → {len(matched_jobs)} vagas com match suficiente.")

        new_jobs = deduplicate_and_save(matched_jobs)
        print(f"   → {len(new_jobs)} são novas (não vistas antes).")

        print("\n📨 Enviando relatório ao Telegram...")
        sent = notifier.send_job_report(
            jobs=new_jobs if new_jobs else matched_jobs[:5],
            session_label=session_label,
        )
        if not sent:
            raise RuntimeError("Falha ao enviar mensagem ao Telegram. Verifique TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID e logs da API.")

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        notifier.send_error_alert(str(e))
        raise


if __name__ == "__main__":
    import sys
    label = sys.argv[1] if len(sys.argv) > 1 else "Manual"
    run_agent(session_label=label)
